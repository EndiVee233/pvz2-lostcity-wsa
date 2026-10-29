#include "profile_store.hpp"
#include <iostream>
#include <stdexcept>
using namespace pvz2_recovered;
static unsigned checks = 0;
static void check(bool ok, const char* message) {
    if (!ok) throw std::runtime_error(message);
    ++checks;
}
int main() {
    try {
        ProfileStore s;
        auto first = s.create(U"玩家甲", 100);
        s.create(U"玩家乙", 200);
        check(s.manager.selected_id == 200 && s.profile_count() == 2, "create selection");
        check(select_by_name(s, s.manager, U"玩家甲") && s.manager.selected_id == 100, "select existing");
        check(!select_by_name(s, s.manager, U"missing") && s.manager.selected_id == 100, "missing selection unchanged");
        s.events.clear();
        check(rename_by_name(s, s.manager, U"玩家甲", U"自定义昵称"), "rename");
        check(s.name_of(*s.resolve(first)) == U"自定义昵称", "unicode name retained");
        check(s.events == std::vector<std::string>{"rename", "sync-request"}, "rename sync ordering");
        check(!rename_by_name(s, s.manager, U"missing", U"unused"), "rename missing");
        check(passes_substring_filter(s, U"正常昵称", {}), "empty filter");
        check(!passes_substring_filter(s, U"禁词开头", {U"禁词"}), "match at zero");
        check(!passes_substring_filter(s, U"中间禁词末尾", {U"其它", U"禁词"}), "match inside");
        check(passes_substring_filter(s, U"玩家乙", {U"禁词"}), "no match");
        s.events.clear();
        check(delete_by_name(s, s.manager, U"自定义昵称") == 1 && s.manager.selected_id == 200, "delete and fallback");
        check(s.events == std::vector<std::string>{"notify-delete", "remove", "sync-request"}, "delete ordering");
        check(s.resolve(first) == nullptr, "deleted handle invalid");
        check(delete_by_name(s, s.manager, U"missing") == 0, "delete missing");
        s.events.clear();
        check(delete_by_name(s, s.manager, U"玩家乙") == 2 && s.manager.selected_id == 0, "last delete");
        check(s.events == std::vector<std::string>{"notify-delete", "remove"}, "last delete no sync");
        check(!select_first_available(s, s.manager), "empty fallback");
        std::cout << "PASS " << checks << " profile lifecycle checks\n";
        return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
