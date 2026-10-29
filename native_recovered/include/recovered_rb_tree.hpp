#pragma once
#include <utility>
// Shared recovered ARM/Thumb tree link algorithms. Host node pointer width is intentional.
namespace pvz2_recovered::engine::rb {
// 014e2cf0
template<class Node> Node* next(Node* n) {
    if (n->right) {
        n = n->right;
        while (n->left) n = n->left;
    } else {
        auto* p = n->parent;
        while (n == p->right) { n = p; p = p->parent; }
        if (n->right != p) n = p;
    }
    return n;
}
// 014e2cac
template<class Node> Node* previous(Node* n) {
    if (n->color == 0 && n->parent->parent == n) return n->right;
    if (n->left) {
        n = n->left;
        while (n->right) n = n->right;
    } else {
        auto* p = n->parent;
        while (n == p->left) { n = p; p = p->parent; }
        n = p;
    }
    return n;
}
// 014e2c4c
template<class Node> void rotate_left(Node* n, Node*& root) {
    auto* r = n->right;
    n->right = r->left;
    if (r->left) r->left->parent = n;
    r->parent = n->parent;
    if (root == n) root = r;
    else if (n == n->parent->left) n->parent->left = r;
    else n->parent->right = r;
    r->left = n; n->parent = r;
}
// 014e2c7c
template<class Node> void rotate_right(Node* n, Node*& root) {
    auto* l = n->left;
    n->left = l->right;
    if (l->right) l->right->parent = n;
    l->parent = n->parent;
    if (root == n) root = l;
    else if (n == n->parent->right) n->parent->right = l;
    else n->parent->left = l;
    l->right = n; n->parent = l;
}
// 014e2d78
template<class Node> void insert(Node& header_, bool left, Node* n, Node* parent) {
    n->parent = parent; n->left = n->right = nullptr; n->color = 0;
    if (left) {
        parent->left = n;
        if (parent == &header_) header_.parent = header_.right = n;
        else if (parent == header_.left) header_.left = n;
    } else {
        parent->right = n;
        if (parent == header_.right) header_.right = n;
    }
    while (n != header_.parent && n->parent->color == 0) {
        auto* p = n->parent;
        auto* g = p->parent;
        if (p == g->left) {
            auto* uncle = g->right;
            if (uncle && uncle->color == 0) {
                p->color = uncle->color = 1; g->color = 0; n = g;
            } else {
                if (n == p->right) { n = p; rotate_left(n, header_.parent); }
                n->parent->color = 1; g->color = 0; rotate_right(g, header_.parent);
            }
        } else {
            auto* uncle = g->left;
            if (uncle && uncle->color == 0) {
                p->color = uncle->color = 1; g->color = 0; n = g;
            } else {
                if (n == p->left) { n = p; rotate_right(n, header_.parent); }
                n->parent->color = 1; g->color = 0; rotate_left(g, header_.parent);
            }
        }
    }
    header_.parent->color = 1;
}
// 014e2e64
template<class Node> Node* erase(Node& header_, Node* z) {
    auto* y = z;
    Node* x;
    Node* parent;
    if (!y->left) x = y->right;
    else if (!y->right) x = y->left;
    else { y = y->right; while (y->left) y = y->left; x = y->right; }
    if (y != z) {
        z->left->parent = y; y->left = z->left;
        if (y != z->right) {
            parent = y->parent;
            if (x) x->parent = y->parent;
            y->parent->left = x;
            y->right = z->right; z->right->parent = y;
        } else parent = y;
        if (header_.parent == z) header_.parent = y;
        else if (z->parent->left == z) z->parent->left = y;
        else z->parent->right = y;
        y->parent = z->parent;
        std::swap(y->color, z->color);
        y = z;
    } else {
        parent = y->parent;
        if (x) x->parent = y->parent;
        if (header_.parent == z) header_.parent = x;
        else if (z->parent->left == z) z->parent->left = x;
        else z->parent->right = x;
        if (header_.left == z) {
            if (!z->right) header_.left = z->parent;
            else { header_.left = x; while (header_.left->left) header_.left = header_.left->left; }
        }
        if (header_.right == z) {
            if (!z->left) header_.right = z->parent;
            else { header_.right = x; while (header_.right->right) header_.right = header_.right->right; }
        }
    }
    if (y->color == 1) {
        while (x != header_.parent && (!x || x->color == 1)) {
            if (x == parent->left) {
                auto* sibling = parent->right;
                if (sibling->color == 0) {
                    sibling->color = 1; parent->color = 0; rotate_left(parent, header_.parent); sibling = parent->right;
                }
                if ((!sibling->left || sibling->left->color == 1) && (!sibling->right || sibling->right->color == 1)) {
                    sibling->color = 0; x = parent; parent = parent->parent;
                } else {
                    if (!sibling->right || sibling->right->color == 1) {
                        sibling->left->color = 1; sibling->color = 0; rotate_right(sibling, header_.parent); sibling = parent->right;
                    }
                    sibling->color = parent->color; parent->color = 1;
                    if (sibling->right) sibling->right->color = 1;
                    rotate_left(parent, header_.parent);
                    break;
                }
            } else {
                auto* sibling = parent->left;
                if (sibling->color == 0) {
                    sibling->color = 1; parent->color = 0; rotate_right(parent, header_.parent); sibling = parent->left;
                }
                if ((!sibling->right || sibling->right->color == 1) && (!sibling->left || sibling->left->color == 1)) {
                    sibling->color = 0; x = parent; parent = parent->parent;
                } else {
                    if (!sibling->left || sibling->left->color == 1) {
                        sibling->right->color = 1; sibling->color = 0; rotate_left(sibling, header_.parent); sibling = parent->left;
                    }
                    sibling->color = parent->color; parent->color = 1;
                    if (sibling->left) sibling->left->color = 1;
                    rotate_right(parent, header_.parent);
                    break;
                }
            }
        }
        if (x) x->color = 1;
    }
    return y;
}
}
