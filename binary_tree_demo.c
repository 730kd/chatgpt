#include <stdio.h>
#include <stdlib.h>

// 二叉搜索树节点
typedef struct Node {
    int value;
    struct Node *left;
    struct Node *right;
} Node;

Node *create_node(int value) {
    Node *node = (Node *)malloc(sizeof(Node));
    if (!node) {
        perror("malloc failed");
        exit(EXIT_FAILURE);
    }
    node->value = value;
    node->left = NULL;
    node->right = NULL;
    return node;
}

Node *insert(Node *root, int value) {
    if (root == NULL) {
        return create_node(value);
    }

    if (value < root->value) {
        root->left = insert(root->left, value);
    } else if (value > root->value) {
        root->right = insert(root->right, value);
    }
    // 相同值不重复插入
    return root;
}

void preorder(Node *root) {
    if (!root) {
        return;
    }
    printf("%d ", root->value);
    preorder(root->left);
    preorder(root->right);
}

void inorder(Node *root) {
    if (!root) {
        return;
    }
    inorder(root->left);
    printf("%d ", root->value);
    inorder(root->right);
}

void postorder(Node *root) {
    if (!root) {
        return;
    }
    postorder(root->left);
    postorder(root->right);
    printf("%d ", root->value);
}

Node *search(Node *root, int target) {
    if (!root || root->value == target) {
        return root;
    }
    if (target < root->value) {
        return search(root->left, target);
    }
    return search(root->right, target);
}

void free_tree(Node *root) {
    if (!root) {
        return;
    }
    free_tree(root->left);
    free_tree(root->right);
    free(root);
}

int main(void) {
    int data[] = {8, 3, 10, 1, 6, 14, 4, 7, 13};
    int n = (int)(sizeof(data) / sizeof(data[0]));

    Node *root = NULL;
    for (int i = 0; i < n; i++) {
        root = insert(root, data[i]);
    }

    printf("前序遍历: ");
    preorder(root);
    printf("\n");

    printf("中序遍历: ");
    inorder(root);
    printf("\n");

    printf("后序遍历: ");
    postorder(root);
    printf("\n");

    int target = 7;
    Node *found = search(root, target);
    if (found) {
        printf("查找 %d: 找到了\n", target);
    } else {
        printf("查找 %d: 没找到\n", target);
    }

    free_tree(root);
    return 0;
}
