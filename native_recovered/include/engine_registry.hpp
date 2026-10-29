#pragma once
#include "engine_handles.hpp"
#include <array>

namespace pvz2_recovered::engine {
using Descriptor32 = std::array<std::uint32_t, 3>;
// Host views of the original read-only tree links. They are not ARM32 ABI structs.
struct StoreNameNode {
    const StoreNameNode* left = nullptr;
    const StoreNameNode* right = nullptr;
    std::uint32_t name = 0, encoded_type = 0;
};
struct DescriptorNode {
    const DescriptorNode* left = nullptr;
    const DescriptorNode* right = nullptr;
    Descriptor32 key{};
    Handle handle{};
};
struct ObjectNameNode {
    const ObjectNameNode* left = nullptr;
    const ObjectNameNode* right = nullptr;
    std::uint32_t name = 0;
    Descriptor32 descriptor{};
};
struct StoreView {
    std::uint32_t type = 0;
    Slot32* slots = nullptr;
    std::size_t capacity = 0;
    const DescriptorNode* descriptors = nullptr;
    const ObjectNameNode* names = nullptr;
    LazyResolvers* resolvers = nullptr;
};
struct RegistryView {
    std::vector<StoreView*> primary, secondary;
    const StoreNameNode* names = nullptr;
};
struct InternStrings : InternReferences {
    // 011f14cc boundary: obtains an ARM32 text address or an adapter text token,
    // including for ID zero. Canonical lookup only consumes the numeric name ID.
    virtual std::uint32_t text_address(std::uint32_t id) = 0;
};
// The caller owns all views and must keep their trees and slots alive during calls.
// NameIndex owns/writes the name trees; InternPool owns intern storage. This
// header only exposes the read views; complete type construction/RTTI is separate.
StoreView* find_store(const RegistryView&, std::uint32_t encoded_type);
// 011e7570: exact unsigned intern-ID lookup followed by bank selection.
StoreView* find_named_store(const RegistryView&, std::uint32_t name);
// 011e6840: missing/stale handles produce the all-zero descriptor.
Descriptor32 describe_handle(const StoreView&, Handle);
// 011e6890: stored handles must resolve to live slots (an original engine invariant).
Handle handle_from_descriptor(const StoreView&, const Descriptor32&, InternReferences&);
// 011e6a90.
Handle handle_from_name(const StoreView&, std::uint32_t name, InternReferences&);
// 011e761c. Returned value is a newly constructed handle, not an assignment target.
Handle canonical_handle(const RegistryView&, Handle, InternStrings&);
// 001ea034. Lazy resolvers are required only for a matching lazy empty slot.
std::uint32_t resolve_registered_object(const RegistryView&, Handle, InternStrings&);
}
