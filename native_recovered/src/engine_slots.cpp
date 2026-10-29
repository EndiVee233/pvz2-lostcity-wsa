#include "engine_slots.hpp"
#include <stdexcept>

namespace pvz2_recovered::engine {
void SlotPool::discard_storage() {
    std::vector<Slot32>().swap(slots_);
    for (std::uint32_t i = 0; i < 4; ++i) anchors_[i] = {free_list + i, free_list + i};
    counts = {};
}
SlotPool::SlotPool(std::uint32_t type) : type_(type) {
    for (std::uint32_t i = 0; i < 4; ++i) anchors_[i] = {free_list + i, free_list + i};
}
std::uint32_t& SlotPool::link(std::uint32_t token, unsigned word) {
    return token >= free_list ? anchors_[token - free_list][word] : slots_.at(token).unknown00[word];
}
const std::uint32_t& SlotPool::link(std::uint32_t token, unsigned word) const {
    return token >= free_list ? anchors_[token - free_list][word] : slots_.at(token).unknown00[word];
}
void SlotPool::detach(std::uint32_t index) {
    const auto next = link(index, 0), previous = link(index, 1);
    link(previous, 0) = next;
    link(next, 1) = previous;
    link(index, 1) = index;
}
void SlotPool::insert_before(std::uint32_t index, std::uint32_t next) {
    const auto previous = link(next, 1);
    link(index, 0) = next;
    link(index, 1) = previous;
    link(next, 1) = index;
    link(previous, 0) = index;
}
void SlotPool::grow(std::uint32_t capacity) {
    const auto old = static_cast<std::uint32_t>(slots_.size());
    // Original malloc/memset assumes non-shrinking, successful allocation. Host
    // exceptions make misuse explicit; they are not original failure semantics.
    if (capacity < old || capacity > 0x1000000U) throw std::invalid_argument("slot growth capacity");
    slots_.resize(capacity);
    for (auto i = old; i < capacity; ++i) {
        slots_[i].generation = 1;
        insert_before(i, link(free_list, 0));
    }
    counts.free += capacity - old;
}
std::uint32_t SlotPool::take_slot() {
    if (link(free_list, 1) == free_list) {
        const auto capacity = static_cast<std::uint32_t>(slots_.size());
        grow(capacity + (capacity < 0x200U ? 0x100U : capacity >> 1));
    }
    const auto index = link(free_list, 1);
    detach(index);
    insert_before(index, active_list);
    --counts.free;
    return index;
}
void SlotPool::recycle(std::uint32_t index, bool defer) {
    detach(index);
    if (defer) {
        insert_before(index, deferred_list);
        ++counts.deferred;
    } else if (index < 0x10000U && slots_[index].generation < 0xfffffffeU) {
        insert_before(index, free_list);
        ++counts.free;
    } else if (index >= 0x10000U && slots_[index].generation < 0xffffffU) {
        insert_before(index, link(free_list, 0));
        ++counts.free;
    } else {
        insert_before(index, retired_list);
        ++counts.retired;
    }
}
Handle SlotPool::packed(std::uint32_t index) const {
    const auto generation = slots_[index].generation;
    if (index < 0x10000U) return {index | (generation << 16), (type_ << 17) | (generation >> 16)};
    return {index | (generation << 24), (type_ << 17) | (generation >> 8) | 0x10000U};
}
Handle SlotPool::create(std::uint32_t object, int mode_value, std::uint8_t marked,
                        const Descriptor32* descriptor, std::uint32_t descriptor_seed, SlotServices& services) {
    const auto index = take_slot();
    auto& s = slots_[index];
    s.flags = (s.flags + 1) | (marked ? 0x90000000U : 0x80000000U);
    ++counts.live;
    s.object_address = object;
    s.flags = (s.flags & 0x9fffffffU) |
        (mode_value == 1 ? 0x40000000U : mode_value == 2 ? 0x20000000U : 0U);
    const auto handle = packed(index);
    const Descriptor32 value = descriptor ? *descriptor : Descriptor32{
        index, s.generation, (handle.high & 0x40000000U) ? 0xffffffffU : descriptor_seed};
    for (unsigned i = 0; i < 3; ++i) s.unknown14[i] = value[i];
    services.put_descriptor(value, handle);
    const auto count = services.callback_count(SlotEvent::created);
    for (std::size_t i = 0; i < count; ++i) services.callback(SlotEvent::created, i, handle);
    return handle;
}
StoreView SlotPool::view() { return {type_, slots_.data(), slots_.size(), nullptr, nullptr, nullptr}; }
void SlotPool::retain(Handle h) {
    if (auto* s = lookup_slot(type_, slots_.data(), slots_.size(), h)) ++s->flags;
}
bool SlotPool::release(Handle h, SlotServices& services) {
    auto* s = lookup_slot(type_, slots_.data(), slots_.size(), h);
    if (!s) return false;
    auto flags = --s->flags;
    if (flags & 0x3ffffffU) return true;
    const auto count = services.callback_count(SlotEvent::before_release);
    for (std::size_t i = 0; i < count; ++i) services.callback(SlotEvent::before_release, i, h);
    // Callbacks must not grow/move slots: the original keeps the raw slot pointer.
    if (count) flags = s->flags;
    --counts.live;
    s->flags = 0;
    services.erase_descriptor({s->unknown14[0], s->unknown14[1], s->unknown14[2]});
    ++s->generation;
    for (auto& word : s->unknown14) word = 0;
    const bool defer = (flags & 0x40000000U) != 0;
    if (!defer && s->object_address) {
        if (!(flags & 0x20000000U)) services.destroy_object(s->object_address);
        s->object_address = 0;
    }
    recycle(decode(h).index, defer);
    return true;
}
std::uint32_t SlotPool::reference_count(Handle h) {
    const auto* s = lookup_slot(type_, slots_.data(), slots_.size(), h);
    return s ? s->flags & 0x3ffffffU : 0;
}
void SlotPool::drain_deferred(SlotServices& services) {
    auto index = link(deferred_list, 1);
    while (index != deferred_list) {
        auto& s = slots_[index];
        if (s.object_address) {
            services.destroy_object(s.object_address);
            s.object_address = 0;
        }
        recycle(index, false);
        index = link(deferred_list, 1);
    }
    counts.deferred = 0;
}
bool SlotPool::set_object(Handle h, std::uint32_t object) {
    auto* s = lookup_slot(type_, slots_.data(), slots_.size(), h);
    if (!s) return false;
    s->object_address = object;
    return true;
}
bool SlotPool::set_mode(Handle h, int value) {
    auto* s = lookup_slot(type_, slots_.data(), slots_.size(), h);
    if (!s) return false;
    s->flags = (s->flags & 0x9fffffffU) | (value == 1 ? 0x40000000U : value == 2 ? 0x20000000U : 0U);
    return true;
}
std::uint32_t SlotPool::mode(Handle h) {
    const auto* s = lookup_slot(type_, slots_.data(), slots_.size(), h);
    return !s || (s->flags & 0x20000000U) ? 2U : (s->flags >> 30) & 1U;
}
bool SlotPool::set_bit28(Handle h, int value) {
    auto* s = lookup_slot(type_, slots_.data(), slots_.size(), h);
    if (!s) return false;
    s->flags = value ? s->flags | 0x10000000U : s->flags & 0xefffffffU;
    return true;
}
bool SlotPool::bit28(Handle h) {
    const auto* s = lookup_slot(type_, slots_.data(), slots_.size(), h);
    return s && (s->flags & 0x10000000U);
}
bool SlotPool::set_lazy(Handle h, int value) {
    auto* s = lookup_slot(type_, slots_.data(), slots_.size(), h);
    if (!s) return false;
    s->flags = value ? s->flags | 0x08000000U : s->flags & 0xf7ffffffU;
    return true;
}
bool SlotPool::lazy(Handle h) {
    const auto* s = lookup_slot(type_, slots_.data(), slots_.size(), h);
    return s && (s->flags & 0x08000000U);
}
std::vector<std::uint32_t> SlotPool::list(std::uint32_t anchor) const {
    if (anchor < free_list) throw std::invalid_argument("slot list anchor");
    std::vector<std::uint32_t> result;
    auto previous = anchor;
    for (auto i = link(anchor, 0); i != anchor; i = link(i, 0)) {
        if (result.size() >= slots_.size() || link(i, 1) != previous)
            throw std::logic_error("invalid slot list");
        result.push_back(i);
        previous = i;
    }
    if (link(anchor, 1) != previous) throw std::logic_error("invalid slot list tail");
    return result;
}
}
