"""
Comprehensive dataset generator using the [DRAW] engine.

Generates hand-drawn diagrams for every CS teaching scenario by
prompting Ollama with the DRAW reference and topic-specific instructions.

Usage:
    python generate_draw_dataset.py --topic "binary_search_tree" --count 3
    python generate_draw_dataset.py --all --count 2
    python generate_draw_dataset.py --category trees --count 3
"""

import json, os, sys, argparse, time, re, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).parent

# Load the DRAW reference
with open(HERE / 'DRAW_REFERENCE.md') as f:
    DRAW_REF = f.read()

SYSTEM_PROMPT = f"""You are an expert at creating hand-drawn diagrams for computer science education.
You output diagrams using the [DRAW]...[/DRAW] tag format.

{DRAW_REF}

## CRITICAL RULES
1. Output ONLY the [DRAW]...[/DRAW] block — no explanations, no markdown fences.
2. Every diagram must be self-contained within one [DRAW]...[/DRAW] block.
3. Use proper coordinates — space elements 20-40px apart.
4. Keep diagrams clean: 5-20 primitives per diagram.
5. Use TEXT for all labels. Use center=true for node labels.
6. Use CIRCLE for tree/graph nodes (radius 18-22), RECT for boxes.
7. Use ARROW for directed edges, LINE for undirected.
8. Use HIGHLIGHT to emphasize important cells or regions.
9. Use GRID for tables and arrays.
10. Use POLYGON for diamond shapes (flowchart decisions).
11. Vary line styles: use style=smooth for clean diagrams, style=wobbly for sketchy feel.
12. Coordinates: x increases right, y increases down. Start from (10,10) or similar.
"""

# ═══════════════════════════════════════════════════════════════════════
#  Topic definitions — 50+ CS teaching scenarios
# ═══════════════════════════════════════════════════════════════════════

TOPICS = {
    # ── Data Structures ──
    "array_indexing": {
        "category": "data_structures",
        "prompt": """Draw an array diagram showing 6 elements with their indices.
Values: [10, 25, 8, 42, 17, 3]. Show indices 0-5 below each cell.
Use GRID for the array structure and TEXT for values and indices.
Make it clean and clear — a student's first introduction to arrays.""",
    },
    "array_insertion": {
        "category": "data_structures",
        "prompt": """Draw a BEFORE and AFTER diagram showing insertion into an array at index 2.
BEFORE: [A, B, D, E] with indices 0-3.
AFTER: [A, B, C, D, E] with indices 0-4.
Show the shift operation with an arrow. Use two GRID sections side by side.
Label them "Before" and "After".""",
    },
    "singly_linked_list": {
        "category": "data_structures",
        "prompt": """Draw a singly linked list with 4 nodes: head -> 10 -> 20 -> 30 -> null.
Each node should be a RECT with a divider line separating data and next-pointer.
Use ARROW between nodes. Show the head pointer with a label.
Make the null terminator clear with an X or diagonal line.""",
    },
    "doubly_linked_list": {
        "category": "data_structures",
        "prompt": """Draw a doubly linked list with 3 nodes: A <-> B <-> C.
Each node has prev and next pointers. Show arrows going both directions.
Use RECT for nodes, ARROW for pointers. Label prev/next clearly.""",
    },
    "linked_list_insert_head": {
        "category": "data_structures",
        "prompt": """Draw BEFORE and AFTER diagrams for inserting at the head of a linked list.
BEFORE: head -> [20] -> [30] -> null
AFTER: head -> [10] -> [20] -> [30] -> null
Show the pointer reassignment with a curved arrow. Use two sections side by side.""",
    },
    "linked_list_delete": {
        "category": "data_structures",
        "prompt": """Draw BEFORE and AFTER diagrams for deleting node [20] from a linked list.
BEFORE: head -> [10] -> [20] -> [30] -> null
AFTER: head -> [10] -> [30] -> null
Show the bypass arrow. Use HIGHLIGHT on the deleted node in the BEFORE diagram.""",
    },
    "stack_push_pop": {
        "category": "data_structures",
        "prompt": """Draw a stack diagram showing 3 states:
1. Empty stack
2. After push(5), push(3), push(8) — show "top" label
3. After pop() — 8 is removed, top moves to 3
Use RECT for stack elements, stack them vertically. Label "top" with an arrow.""",
    },
    "queue_enqueue_dequeue": {
        "category": "data_structures",
        "prompt": """Draw a queue diagram showing:
1. Empty queue
2. After enqueue(A), enqueue(B), enqueue(C) — show "front" and "rear" labels
3. After dequeue() — A is removed, front moves to B
Use RECT for elements in a horizontal row. Label front and rear clearly.""",
    },
    "circular_queue": {
        "category": "data_structures",
        "prompt": """Draw a circular queue with capacity 5, currently holding [B, C, D].
Show the circular buffer as 5 cells in a row with wraparound arrows.
Mark front at B (index 1) and rear at D (index 3). Show empty cells at indices 0 and 4.
Use GRID for the buffer cells.""",
    },
    "binary_search_tree": {
        "category": "data_structures",
        "prompt": """Draw a balanced BST with 7 nodes: root=8, left=3, right=10, 3's children=1,6, 10's children=null,14, 6's children=4,7.
Use CIRCLE for nodes (radius 18), LINE for edges, TEXT for values.
Make it look like a proper tree with the root at top center.
Add a small note: "BST property: left < root < right".""",
    },
    "bst_insert": {
        "category": "data_structures",
        "prompt": """Draw a BST insertion walkthrough. Show the tree BEFORE inserting 5, then AFTER.
BEFORE: root=8, left=3 (children: 1,6 with 4), right=10.
Show the search path with dashed arrows: 8->3->6->4->(insert 5 as right child of 4).
AFTER: same tree with 5 added as right child of 4.
Use style=dashed for the search path.""",
    },
    "bst_delete_cases": {
        "category": "data_structures",
        "prompt": """Draw the three BST deletion cases side by side:
Case 1 (Leaf): Delete node 1 — just remove it.
Case 2 (One child): Delete node 6 (has left child 4) — replace with child.
Case 3 (Two children): Delete node 3 — find inorder successor (4), copy up, delete successor.
Show BEFORE and AFTER for each case. Use three columns.""",
    },
    "avl_rotation_ll": {
        "category": "data_structures",
        "prompt": """Draw an AVL tree LL (left-left) rotation.
BEFORE: root=30 (balance=+2), left=20 (balance=+1), 20's left=10.
AFTER: root=20, left=10, right=30.
Show the rotation with a curved arrow. Label balance factors.
Use CIRCLE for nodes, include balance factor as small text above each node.""",
    },
    "avl_rotation_rr": {
        "category": "data_structures",
        "prompt": """Draw an AVL tree RR (right-right) rotation.
BEFORE: root=10 (balance=-2), right=20 (balance=-1), 20's right=30.
AFTER: root=20, left=10, right=30.
Show the rotation with a curved arrow. Label balance factors.""",
    },
    "avl_rotation_lr": {
        "category": "data_structures",
        "prompt": """Draw an AVL tree LR (left-right) rotation — two steps.
Step 1: RR rotation on left child.
Step 2: LL rotation on root.
BEFORE: root=30, left=10, 10's right=20.
AFTER: root=20, left=10, right=30.
Show both steps with arrows.""",
    },
    "heap_min": {
        "category": "data_structures",
        "prompt": """Draw a min-heap as both a tree AND an array.
Tree: root=1, children=3,5, grandchildren=7,9,8,10.
Array: [1, 3, 5, 7, 9, 8, 10] with indices 0-6.
Show the parent-child index relationship: parent(i) = (i-1)//2, left(i)=2i+1, right(i)=2i+2.
Use two sections: tree on left, array on right.""",
    },
    "heap_insert": {
        "category": "data_structures",
        "prompt": """Draw a min-heap insert operation. Insert value 2 into heap [1,3,5,7,9,8,10].
Step 1: Add 2 at the end (as child of 5).
Step 2: Bubble up — swap 2 with 5, then swap 2 with 3.
Show the bubbling path with arrows. Final heap: [1,2,5,7,3,8,10,9].
Show both tree and array views.""",
    },
    "heap_extract_min": {
        "category": "data_structures",
        "prompt": """Draw a min-heap extract-min operation from heap [1,3,5,7,9,8,10].
Step 1: Remove root (1), replace with last element (10).
Step 2: Bubble down — swap 10 with smaller child (3), then with smaller child (7).
Show the bubbling path. Final heap: [3,7,5,10,9,8].
Show both tree and array views.""",
    },
    "hash_table_chaining": {
        "category": "data_structures",
        "prompt": """Draw a hash table with chaining (separate chaining).
Hash table has 5 buckets (indices 0-4). Hash function: h(k) = k mod 5.
Insert: 12, 7, 22, 15, 3, 27.
Show the array of buckets with linked lists hanging off each bucket.
Use RECT for buckets, small linked list nodes for chains.
Label the hash function.""",
    },
    "hash_table_open_addressing": {
        "category": "data_structures",
        "prompt": """Draw a hash table with linear probing (open addressing).
Table size 7. Hash: h(k) = k mod 7.
Insert: 10 (goes to 3), 22 (goes to 1), 31 (3 is taken, probe to 4), 17 (3,4,5 taken, probe to 6).
Show the probing path for 17 with arrows. Mark occupied cells.
Use GRID for the table.""",
    },
    "trie_prefix_tree": {
        "category": "data_structures",
        "prompt": """Draw a trie (prefix tree) containing words: "cat", "car", "cart", "dog", "dot".
Root is empty. Each edge is a letter. Nodes with words are marked with a double circle or DOT.
Show the shared prefixes clearly. Use CIRCLE for nodes, TEXT on edges.
Make it clear how "car" and "cart" share the "car" prefix.""",
    },
    "graph_undirected": {
        "category": "data_structures",
        "prompt": """Draw an undirected graph with 5 vertices (A,B,C,D,E) and 6 edges.
Edges: A-B, A-C, B-D, C-D, C-E, D-E.
Use CIRCLE for vertices, LINE for edges (no arrowheads for undirected).
Position vertices in a pentagon shape. Label each vertex.""",
    },
    "graph_directed": {
        "category": "data_structures",
        "prompt": """Draw a directed graph (digraph) with 5 vertices (A,B,C,D,E) and 7 edges.
Edges: A->B, A->C, B->D, C->B, C->D, D->E, E->A.
Use CIRCLE for vertices, ARROW for directed edges.
Position in a roughly circular layout.""",
    },
    "graph_weighted": {
        "category": "data_structures",
        "prompt": """Draw a weighted directed graph with 5 vertices (S,A,B,C,D).
Edges with weights: S->A(2), S->B(6), A->B(3), A->C(1), B->D(5), C->D(2).
Use CIRCLE for vertices, ARROW for edges, TEXT for weights at edge midpoints.
Position: S left, A top-center, B bottom-center, C top-right, D bottom-right.""",
    },
    "adjacency_matrix": {
        "category": "data_structures",
        "prompt": """Draw an adjacency matrix for a graph with vertices A,B,C,D.
Edges: A->B, A->C, B->D, C->D.
Show the 4x4 matrix with 0s and 1s. Row labels and column labels are A,B,C,D.
Use GRID for the matrix. Highlight the 1s with HIGHLIGHT.""",
    },
    "adjacency_list": {
        "category": "data_structures",
        "prompt": """Draw an adjacency list for a graph with vertices A,B,C,D.
Edges: A->B, A->C, B->D, C->B, C->D.
Show an array of 4 linked lists. Each array entry points to a list of neighbors.
Use RECT for array entries, small linked list nodes for neighbors, ARROW for pointers.""",
    },

    # ── Algorithms: Sorting ──
    "bubble_sort_pass": {
        "category": "algorithms_sorting",
        "prompt": """Draw one pass of bubble sort on array [5, 3, 8, 1, 4].
Show the array at each comparison+swap step within the pass.
Use 5-6 array snapshots. Highlight the elements being compared.
Show the largest element "bubbling" to the end. Use HIGHLIGHT for swapped elements.""",
    },
    "selection_sort": {
        "category": "algorithms_sorting",
        "prompt": """Draw selection sort on array [29, 10, 14, 37, 13].
Show 4 steps (one per iteration). At each step, highlight:
- The unsorted portion
- The minimum element found
- The swap
Use multiple array rows. Label each step "Pass 1", "Pass 2", etc.""",
    },
    "insertion_sort": {
        "category": "algorithms_sorting",
        "prompt": """Draw insertion sort on array [5, 2, 4, 6, 1, 3].
Show the array after each insertion. Highlight the "key" being inserted
and the sorted portion growing from left to right.
Use 6 array snapshots. Label the sorted and unsorted portions.""",
    },
    "merge_sort_tree": {
        "category": "algorithms_sorting",
        "prompt": """Draw the merge sort recursion tree for array [38, 27, 43, 3, 9, 82, 10].
Show the full divide-and-conquer tree:
- Top: [38,27,43,3,9,82,10]
- Split into [38,27,43,3] and [9,82,10]
- Continue splitting until single elements
- Show merge steps going back up with sorted subarrays
Use a tree layout with TEXT for array values at each node.""",
    },
    "quick_sort_partition": {
        "category": "algorithms_sorting",
        "prompt": """Draw one partition step of quicksort on array [8, 3, 1, 7, 0, 10, 2].
Pivot = 2 (last element). Show:
1. Initial array with pivot marked
2. The i and j pointers moving
3. Elements being swapped
4. Final position of pivot
Use multiple array snapshots. Highlight the pivot. Show i and j with arrows.""",
    },
    "heap_sort": {
        "category": "algorithms_sorting",
        "prompt": """Draw heapsort on array [4, 10, 3, 5, 1].
Step 1: Build max-heap — show the heapify process.
Step 2: Repeatedly extract max and place at end.
Show the array and heap tree view side by side at each major step.
Use 4-5 steps total.""",
    },

    # ── Algorithms: Searching ──
    "binary_search": {
        "category": "algorithms_searching",
        "prompt": """Draw binary search for value 23 in sorted array [2,5,8,12,16,23,38,45,56,72].
Show 3 steps with the array, marking low, mid, high pointers at each step.
Step 1: low=0, high=9, mid=4 (value 16) — 23>16, go right.
Step 2: low=5, high=9, mid=7 (value 45) — 23<45, go left.
Step 3: low=5, high=6, mid=5 (value 23) — FOUND!
Use arrows pointing to low, mid, high. Highlight the mid element each step.""",
    },
    "linear_search": {
        "category": "algorithms_searching",
        "prompt": """Draw linear search for value 42 in array [10,25,8,42,17,3].
Show the array with a pointer moving left to right, checking each element.
Highlight the current element being checked. Show "FOUND at index 3" at the end.
Use 4 snapshots or one diagram with numbered steps.""",
    },

    # ── Algorithms: Graph ──
    "bfs_traversal": {
        "category": "algorithms_graph",
        "prompt": """Draw BFS traversal on a graph with vertices A,B,C,D,E,F.
Edges: A-B, A-C, B-D, B-E, C-F, D-F.
Start from A. Show:
1. The graph with nodes
2. The BFS queue at each step (4-5 steps)
3. The BFS tree (discovery edges as solid, cross edges as dashed)
Use CIRCLE for nodes, ARROW for discovery edges, LINE style=dashed for cross edges.
Show the queue as a horizontal list below the graph.""",
    },
    "dfs_traversal": {
        "category": "algorithms_graph",
        "prompt": """Draw DFS traversal on a graph with vertices A,B,C,D,E,F.
Edges: A-B, A-C, B-D, B-E, C-F, D-F.
Start from A. Show:
1. The graph with discovery/finish times on each node
2. Edge classification: tree edges (solid), back edges (dashed), forward/cross (dotted)
Use CIRCLE for nodes. Write "1/12" style discovery/finish times near each node.
Use different line styles for edge types.""",
    },
    "dijkstra_algorithm": {
        "category": "algorithms_graph",
        "prompt": """Draw Dijkstra's algorithm on a weighted graph.
Vertices: S, A, B, C, D.
Edges: S->A(2), S->B(6), A->B(3), A->C(1), B->D(5), C->D(2).
Show:
1. The graph with edge weights
2. A distance table that updates at each step (5-6 rows)
3. The final shortest-path tree (highlighted edges)
Use CIRCLE for nodes, ARROW for edges, TEXT for weights.
Use GRID for the distance table.""",
    },
    "kruskal_mst": {
        "category": "algorithms_graph",
        "prompt": """Draw Kruskal's algorithm for Minimum Spanning Tree.
Graph with vertices A,B,C,D,E,F.
Edges sorted by weight: C-D(1), A-B(2), D-E(3), B-C(4), A-D(5), E-F(6), B-E(7), C-F(8).
Show 4-5 steps as edges are added. Mark accepted edges with thick lines,
rejected edges (would create cycle) with dashed lines.
Use CIRCLE for vertices, LINE for edges. Use style=thick (width=4) for MST edges.""",
    },
    "prim_mst": {
        "category": "algorithms_graph",
        "prompt": """Draw Prim's algorithm for Minimum Spanning Tree starting from vertex A.
Same graph as Kruskal example. Show the growing tree:
Step 1: Start at A, add A-B(2)
Step 2: From {A,B}, add B-C(4)
Step 3: From {A,B,C}, add C-D(1)
Step 4: From {A,B,C,D}, add D-E(3)
Step 5: From {A,B,C,D,E}, add E-F(6)
Highlight the MST edges. Show the "frontier" edges being considered at each step.""",
    },
    "topological_sort": {
        "category": "algorithms_graph",
        "prompt": """Draw topological sort on a DAG with vertices A,B,C,D,E,F.
Edges: A->C, A->D, B->C, B->E, C->F, D->F, E->F.
Show:
1. The DAG
2. The in-degree table
3. The queue at each step
4. The final topological order
Use CIRCLE for nodes, ARROW for edges. Show the order as a horizontal list at bottom.""",
    },
    "bellman_ford": {
        "category": "algorithms_graph",
        "prompt": """Draw Bellman-Ford algorithm on a graph with a negative edge.
Vertices: S, A, B, C, D.
Edges: S->A(4), S->B(5), A->C(3), B->A(-2), B->C(2), C->D(1), D->B(-1).
Show the distance table after each of the 4 relaxation rounds.
Highlight how the negative edge B->A(-2) improves distances in later rounds.
Use GRID for the distance table. Show the graph above the table.""",
    },
    "floyd_warshall": {
        "category": "algorithms_graph",
        "prompt": """Draw Floyd-Warshall all-pairs shortest path on a small graph.
Vertices: 1,2,3,4.
Edges: 1->2(3), 1->4(7), 2->1(8), 2->3(2), 3->1(5), 3->4(1), 4->1(2).
Show the 4x4 distance matrix at k=0 (initial), k=1, k=2, and k=4 (final).
Use GRID for each matrix. Highlight cells that change at each step with HIGHLIGHT.""",
    },

    # ── Dynamic Programming ──
    "dp_fibonacci_memo": {
        "category": "algorithms_dp",
        "prompt": """Draw the memoized Fibonacci recursion tree for fib(5).
Show the tree with nodes for each call. Mark nodes that are computed (not recomputed)
with a checkmark or different style. Show the memoization array at the bottom:
memo[0]=0, memo[1]=1, memo[2]=1, memo[3]=2, memo[4]=3, memo[5]=5.
Use CIRCLE for tree nodes, TEXT for values. Use HIGHLIGHT for memoized results.""",
    },
    "dp_knapsack_table": {
        "category": "algorithms_dp",
        "prompt": """Draw the 0/1 Knapsack DP table for:
Items: (w=2,v=3), (w=3,v=4), (w=4,v=5), (w=5,v=6). Capacity W=8.
Show the full 5x9 DP table with all values filled.
Highlight the cell dp[4][8]=10 (final answer).
Draw dependency arrows from dp[4][8] to dp[3][8] and dp[3][3].
Use GRID for the table. Use HIGHLIGHT for the answer cell. Use ARROW for dependencies.""",
    },
    "dp_lcs_table": {
        "category": "algorithms_dp",
        "prompt": """Draw the LCS DP table for strings X="ABCBDAB" and Y="BDCABA".
Show a 6x6 portion of the table (enough to illustrate).
Draw the backtracking path from bottom-right to top-left with ARROWs.
Mark cells where characters match with a small DOT or different style.
Show the resulting LCS: "BCBA" at the bottom.
Use GRID for the table. Use HIGHLIGHT for the backtracking path.""",
    },
    "dp_edit_distance_table": {
        "category": "algorithms_dp",
        "prompt": """Draw the Edit Distance DP table for "kitten" -> "sitting".
Show the full 7x8 table. Highlight the path from dp[0][0] to dp[6][7]=3.
Show the edit operations along the path: sub(k->s), sub(e->i), ins(g).
Use GRID for the table. Use ARROW for the path. Label operations beside the path.""",
    },
    "dp_coin_change": {
        "category": "algorithms_dp",
        "prompt": """Draw the Coin Change DP table for coins [1,2,5] and amount=11.
Show the 1D DP array dp[0..11] where dp[i] = min coins for amount i.
Show how dp[11] is computed from dp[10], dp[9], dp[6].
Use an array diagram with indices. Draw arrows showing dependencies.
Highlight dp[11]=3 (coins: 5+5+1).""",
    },
    "dp_rod_cutting": {
        "category": "algorithms_dp",
        "prompt": """Draw the Rod Cutting DP table for rod length 8.
Prices: [1,5,8,9,10,17,17,20] for lengths 1-8.
Show the 1D DP array. For each length, show which cut produces the max value.
Use an array diagram. Draw arrows from dp[i] to dp[i-j] + price[j].
Highlight the optimal cuts for length 8: 2+6 (5+17=22).""",
    },
    "dp_matrix_chain": {
        "category": "algorithms_dp",
        "prompt": """Draw the Matrix Chain Multiplication DP table.
Matrices: A1(30x35), A2(35x15), A3(15x5), A4(5x10), A5(10x20), A6(20x25).
Show the 6x6 upper-triangular DP table. Fill in a few key cells.
Show the split points. Highlight the optimal parenthesization.
Use GRID for the table. Use TEXT for values and split points.""",
    },

    # ── Trees ──
    "tree_traversals_visual": {
        "category": "trees",
        "prompt": """Draw a binary tree and show all four traversals visually.
Tree: root=4, left=2 (children: 1,3), right=6 (children: 5,7).
Draw the tree once, then show four traversal paths with different colored/style arrows:
- Inorder: trace the path 1->2->3->4->5->6->7
- Preorder: trace 4->2->1->3->6->5->7
- Postorder: trace 1->3->2->5->7->6->4
- Level-order: show levels with brackets
Use one tree diagram with numbered steps or four small diagrams.""",
    },
    "expression_tree": {
        "category": "trees",
        "prompt": """Draw an expression tree for: (a + b) * (c - d) / e.
Show the tree with operators at internal nodes and operands at leaves.
Then show the postorder traversal that produces the postfix expression: a b + c d - * e /.
Use CIRCLE for nodes. Write the expression below the tree.""",
    },
    "segment_tree": {
        "category": "trees",
        "prompt": """Draw a segment tree for array [1, 3, 5, 7, 9, 11].
Show the full binary tree where each node stores the sum of its range.
Root: sum of [0..5] = 36. Leaves: individual elements.
Internal nodes show the range and sum.
Use CIRCLE for nodes. Write "range: sum" in each node.""",
    },
    "fenwick_tree": {
        "category": "trees",
        "prompt": """Draw a Fenwick tree (Binary Indexed Tree) for array [3, 2, -1, 6, 5, 4, -3, 3].
Show the tree structure AND the array representation.
For each node, show which range it covers.
Show how to compute prefix sum up to index 5 using the tree.
Use a tree diagram on top and array below.""",
    },
    "red_black_tree": {
        "category": "trees",
        "prompt": """Draw a red-black tree with 7 nodes.
Use different styles: filled circles for black nodes, empty circles for red nodes.
Root is black. Show the black-height on each path.
Insert sequence: 10, 5, 15, 3, 7, 12, 17.
Use CIRCLE with fill=light for red nodes, regular CIRCLE for black nodes.
Label each node with its value.""",
    },
    "b_tree": {
        "category": "trees",
        "prompt": """Draw a B-tree of order 3 (2-3 tree) with keys: 10, 20, 5, 15, 25, 8, 12, 18, 28, 3.
Show the tree structure with nodes that can hold 1 or 2 keys.
Use RECT for nodes (wider to hold multiple keys). Show the splitting process
for at least one node. Use ARROW for parent-child pointers.""",
    },

    # ── Memory & Pointers ──
    "stack_vs_heap": {
        "category": "memory",
        "prompt": """Draw a memory layout showing the stack and heap.
Stack (grows down): main() frame with local variables x=5, y=10.
Heap (grows up): dynamically allocated array [1,2,3] at address 0x2000.
Show the stack pointer and the pointer from stack to heap.
Use RECT for memory regions. Label addresses. Use ARROW for pointers.
Add a dividing line between stack and heap regions.""",
    },
    "pointer_arithmetic": {
        "category": "memory",
        "prompt": """Draw pointer arithmetic on an array.
Array: [10, 20, 30, 40, 50] at addresses 0x100, 0x104, 0x108, 0x10C, 0x110.
int *p = &arr[1] (points to 20 at 0x104).
Show: *(p+2) = arr[3] = 40 (at 0x10C).
Use RECT for array cells. Show addresses above cells. Use ARROW for the pointer.
Highlight the element accessed by *(p+2).""",
    },
    "dangling_pointer": {
        "category": "memory",
        "prompt": """Draw a dangling pointer scenario.
Step 1: int *p = malloc(sizeof(int)); *p = 42; — p points to valid heap memory.
Step 2: free(p); — memory is freed but p still holds the address.
Step 3: *p = 99; — DANGER! Writing to freed memory.
Show the three steps. Use HIGHLIGHT on the freed memory. Mark the danger with a warning symbol.
Use RECT for memory, ARROW for pointers.""",
    },
    "memory_leak": {
        "category": "memory",
        "prompt": """Draw a memory leak scenario.
Step 1: int *p = malloc(100); — p points to 100 bytes on heap.
Step 2: p = malloc(200); — p now points to new memory. Old 100 bytes are LEAKED!
Show the orphaned memory block with no pointer to it. Use HIGHLIGHT on the leaked block.
Label it "LEAKED — unreachable". Use RECT for memory blocks, ARROW for pointers.""",
    },

    # ── Flowcharts & State Machines ──
    "algorithm_flowchart": {
        "category": "flowcharts",
        "prompt": """Draw a flowchart for: "Read number n. If n < 0, print 'Negative'. Else if n == 0, print 'Zero'. Else print 'Positive'."
Use RECT for process steps, POLYGON (diamond) for decisions, ARROW for flow.
Start at top, branch left/right for decisions, converge at bottom.
Use TEXT for labels inside shapes.""",
    },
    "recursion_flow": {
        "category": "flowcharts",
        "prompt": """Draw a flowchart showing the execution flow of recursive factorial(3).
Show the call stack growing: fact(3) calls fact(2) calls fact(1) returns 1.
Then unwinding: fact(2)=2, fact(3)=6.
Use stacked RECT for call frames. Use ARROW for call/return.
Show the return values flowing back up.""",
    },
    "state_machine": {
        "category": "flowcharts",
        "prompt": """Draw a finite state machine for a traffic light.
States: GREEN, YELLOW, RED.
Transitions: GREEN -> YELLOW (timer), YELLOW -> RED (timer), RED -> GREEN (timer).
Use CIRCLE for states. Use ARROW for transitions with labels.
Make it a circular layout. Use fill=light for the current state.""",
    },
    "dfa_string_matching": {
        "category": "flowcharts",
        "prompt": """Draw a DFA (Deterministic Finite Automaton) that recognizes strings ending with "ab".
States: q0 (start), q1 (seen 'a'), q2 (accept, seen 'ab').
Transitions: q0--a-->q1, q0--b-->q0, q1--a-->q1, q1--b-->q2, q2--a-->q1, q2--b-->q0.
Use CIRCLE for states. Double circle for accept state. ARROW for transitions with labels.
Mark the start state with an incoming arrow.""",
    },

    # ── Math & Misc ──
    "number_line": {
        "category": "math",
        "prompt": """Draw a number line from -5 to 5.
Mark integers with small ticks. Label -5, 0, 5.
Highlight the interval [-2, 3] with a thicker line segment.
Mark points -2 and 3 with DOT.
Use LINE for the number line, TEXT for labels, DOT for points.""",
    },
    "venn_diagram": {
        "category": "math",
        "prompt": """Draw a Venn diagram showing two overlapping sets A and B.
Set A = {1, 2, 3, 4}, Set B = {3, 4, 5, 6}.
Intersection A∩B = {3, 4}.
Use CIRCLE for the sets (large, radius ~50). Use TEXT for element labels.
Place elements in the correct regions. Label the sets.""",
    },
    "coordinate_plane": {
        "category": "math",
        "prompt": """Draw a coordinate plane with x and y axes from -4 to 4.
Plot the line y = 2x + 1. Mark 3 points: (-2,-3), (0,1), (2,5).
Use LINE for axes with arrowheads. Use GRID for the grid (light).
Use DOT for points. Use LINE for the plotted line. Label axes and points.""",
    },
    "function_plot": {
        "category": "math",
        "prompt": """Draw a rough plot of f(x) = x² from x=-3 to x=3.
Show the parabola shape. Mark the vertex at (0,0).
Mark points: (-2,4), (-1,1), (0,0), (1,1), (2,4).
Use CURVE for the parabola. Use DOT for points. Use LINE for axes.
Label the function.""",
    },
    "set_notation": {
        "category": "math",
        "prompt": """Draw a visual explanation of set builder notation.
Show: A = { x | x ∈ N, x < 5 } = {1, 2, 3, 4}.
Use BRACE for the curly braces. Use TEXT for the notation.
Show the elements listed out. Use a number line below to highlight the elements.""",
    },
    "big_o_notation": {
        "category": "math",
        "prompt": """Draw a visual comparison of Big-O complexities.
Show a simple graph/plot comparing: O(1), O(log n), O(n), O(n log n), O(n²), O(2ⁿ).
Use different line styles for each curve. Label each curve.
X-axis: "Input size (n)", Y-axis: "Operations".
Use CURVE for the growth curves. Use TEXT for labels.""",
    },

    # ── Logic Gates ──
    "logic_and_gate": {
        "category": "logic_gates",
        "prompt": """Draw a digital logic AND gate.
Inputs A=1, B=0. Output Y=0.
Use RECT or POLYGON for the D-shaped AND gate symbol (flat left, curved right).
Draw two input lines from the left, one output line to the right.
Label inputs A and B, output Y. Show the truth table A B | Y below: 00->0, 01->0, 10->0, 11->1.
Use LINE for wires, TEXT for labels, GRID for the truth table.""",
    },
    "logic_or_gate": {
        "category": "logic_gates",
        "prompt": """Draw a digital logic OR gate.
Inputs A=0, B=1. Output Y=1.
Use a curved shape for the OR gate symbol (concave left, convex right, pointed bottom/top).
Draw two input lines from left, one output line to right. Label inputs and output.
Show the OR truth table below: 00->0, 01->1, 10->1, 11->1.
Use LINE for wires, TEXT for labels, GRID for the truth table.""",
    },
    "logic_not_gate": {
        "category": "logic_gates",
        "prompt": """Draw a digital logic NOT (inverter) gate.
Input A=1, output Y=0. Include the small inversion circle at the output.
Use a triangle pointing right with a CIRCLE (small) at the tip for the bubble.
Show the truth table: 0->1, 1->0.
Use LINE for wires, TEXT for labels, GRID for the truth table.""",
    },
    "logic_xor_gate": {
        "category": "logic_gates",
        "prompt": """Draw a digital logic XOR gate.
Inputs A=1, B=1. Output Y=0.
Show the distinctive double-curved XOR symbol. Inputs from left, output to right.
Show the XOR truth table below: 00->0, 01->1, 10->1, 11->0.
Use LINE for wires, TEXT for labels, GRID for the truth table.""",
    },
    "logic_nand_gate": {
        "category": "logic_gates",
        "prompt": """Draw a digital logic NAND gate.
Inputs A=1, B=1. Output Y=0. AND shape with an inversion bubble at the output.
Show the NAND truth table: 00->1, 01->1, 10->1, 11->0.
Use LINE for wires, CIRCLE for the bubble, TEXT for labels, GRID for the truth table.""",
    },
    "logic_half_adder": {
        "category": "logic_gates",
        "prompt": """Draw a half-adder circuit using XOR and AND gates.
Inputs A, B. Outputs SUM = A XOR B, CARRY = A AND B.
Show the two gates side by side: XOR produces SUM, AND produces CARRY.
Connect inputs with forked wires to both gates. Label inputs, outputs, and internal gates.
Show the truth table for A,B -> SUM,CARRY.
Use LINE for wires, custom shapes for gates, TEXT for labels, GRID for the table.""",
    },
    "logic_full_adder": {
        "category": "logic_gates",
        "prompt": """Draw a full-adder circuit.
Inputs A, B, Cin. Outputs SUM and Cout.
Use two XOR gates, two AND gates, and one OR gate connected in the standard full-adder layout.
Show the carry propagation path with thick lines. Label every input and output.
Use LINE/ARROW for wires, POLYGON/RECT/CIRCLE for gate shapes, TEXT for labels.
Make the diagram clear enough to teach how ripple-carry adders work.""",
    },
    "logic_ripple_carry_adder": {
        "category": "logic_gates",
        "prompt": """Draw a 4-bit ripple-carry adder made of four full-adders chained together.
Inputs: two 4-bit numbers A3A2A1A0 and B3B2B1B0, plus initial carry-in C0.
Outputs: sum S3S2S1S0 and final carry-out C4.
Draw four full-adder blocks as rectangles in a row. Connect carry-out of one to carry-in of the next.
Label A/B bits above, S bits below. Use ARROW for carry propagation direction.
Use RECT for FA blocks, LINE for wires, TEXT for bit labels.""",
    },
    "logic_sr_latch": {
        "category": "logic_gates",
        "prompt": """Draw an SR latch using two cross-coupled NOR gates.
Inputs S (Set) and R (Reset). Outputs Q and Qbar.
Show the feedback loops between the two NOR gates clearly with curved arrows.
Label the stable state when S=0, R=0, Q=1, Qbar=0.
Use curved shapes for NOR gates, CIRCLE for output bubbles, LINE for wires.""",
    },

    # ── Relational Models / Databases ──
    "er_diagram_university": {
        "category": "relational_models",
        "prompt": """Draw an Entity-Relationship (ER) diagram for a university database.
Entities: Student, Course, Professor.
Relationships: Student enrolls in Course (many-to-many, attribute: grade),
Professor teaches Course (one-to-many).
Use RECT for entities. Use a diamond (POLYGON) for relationships.
Show cardinality: 1, N, M labels on the connecting lines.
Use LINE for connections, TEXT for entity names and attributes, POLYGON for diamonds.""",
    },
    "relational_schema_example": {
        "category": "relational_models",
        "prompt": """Draw a relational schema for a simple e-commerce system.
Tables:
- Customers(customer_id PK, name, email)
- Orders(order_id PK, customer_id FK, order_date, total)
- Order_Items(item_id PK, order_id FK, product_id FK, quantity)
- Products(product_id PK, name, price)
Show each table as a rectangle with header (table name + PK) and rows for attributes.
Draw lines between foreign keys and the referenced primary keys.
Use RECT for tables, LINE for relationships, TEXT for attributes. Mark PKs and FKs.""",
    },
    "sql_join_venn": {
        "category": "relational_models",
        "prompt": """Draw a visual explanation of SQL JOINs using overlapping circles.
Two tables: Employees and Departments.
Show INNER JOIN, LEFT JOIN, RIGHT JOIN, FULL OUTER JOIN as labeled Venn-like regions.
Shade the included rows in each case. Label matching key (department_id) in the overlap.
Use CIRCLE for tables, TEXT for labels, HIGHLIGHT to shade included regions.""",
    },
    "normalization_1nf_to_3nf": {
        "category": "relational_models",
        "prompt": """Draw the normalization process from 1NF to 3NF.
1NF table: StudentCourses(student_id, name, course1, course2, course3) — not atomic.
2NF tables: Students(student_id, name), Courses(course_id, title), Enrollments(student_id, course_id).
3NF: split further to remove transitive dependency (move dept info to Departments table).
Show each stage as a set of rectangles. Use arrows to show decomposition.
Use RECT for tables, TEXT for attributes, ARROW for decomposition flow.""",
    },
    "db_index_btree": {
        "category": "relational_models",
        "prompt": """Draw a B+ tree index used in a database.
Internal nodes contain keys [10, 20, 30]. Leaves contain sorted record pointers.
Show root -> internal nodes -> leaf nodes. Leaves are linked horizontally.
Use RECT for nodes, TEXT for keys, LINE/ARROW for parent-child and leaf-chain pointers.
Label one leaf lookup path from root to the leaf containing key 25.""",
    },
    "transaction_schedule": {
        "category": "relational_models",
        "prompt": """Draw a transaction schedule for two transactions T1 and T2.
Operations: T1 reads A, T2 reads A, T1 writes A, T2 writes A, T1 commits, T2 commits.
Show time going left-to-right. Each transaction has its own horizontal line.
Mark operations with symbols (R(A), W(A), C).
Use LINE for timelines, TEXT for operations, ARROW to show time direction.
Highlight a lost-update conflict if present.""",
    },
    "acid_properties": {
        "category": "relational_models",
        "prompt": """Draw a diagram explaining ACID properties of database transactions.
Central box: "ACID Transaction". Four surrounding boxes: Atomicity, Consistency, Isolation, Durability.
Each property has a short example:
- Atomicity: all-or-nothing transfer
- Consistency: balance >= 0
- Isolation: transactions don't interfere
- Durability: committed data survives crash
Use RECT for boxes, LINE for connections, TEXT for labels and examples.""",
    },

    # ── Big Data / Distributed Systems ──
    "mapreduce_wordcount": {
        "category": "big_data",
        "prompt": """Draw the MapReduce data flow for a word-count job.
Input split across 3 mappers. Each mapper emits (word, 1) key-value pairs.
Shuffle/sort groups by key. Reducers sum counts and produce final output.
Show nodes labeled Mapper, Reducer, with input chunks and intermediate key-value streams.
Use RECT for nodes, ARROW for data flow, TEXT for input/output examples.""",
    },
    "hdfs_architecture": {
        "category": "big_data",
        "prompt": """Draw the HDFS architecture with one NameNode and three DataNodes.
NameNode manages metadata. Files are split into blocks (e.g., 128MB) replicated across DataNodes.
Show a file /data/bigfile.txt split into 3 blocks with replication factor 2.
Use RECT for NameNode/DataNodes, smaller RECT for blocks, ARROW for client reads/writes.
Label replication and block placement.""",
    },
    "spark_rdd_lineage": {
        "category": "big_data",
        "prompt": """Draw a Spark RDD lineage graph for a simple word-count job.
RDDs: rawText -> splitWords -> mapToPairs -> reduceByKey -> output.
Show transformations as arrows. Label actions vs transformations.
Use RECT for RDDs, ARROW for transformations, TEXT for operation names.
Show how the lineage graph enables fault tolerance (recompute from parent).""",
    },
    "distributed_consistency_spectrum": {
        "category": "big_data",
        "prompt": """Draw the distributed-system consistency spectrum from Strong Consistency to Eventual Consistency.
Draw a horizontal arrow. Labels from left to right:
Strong Consistency (linearizable), Sequential Consistency, Causal Consistency, Eventual Consistency.
For each, give one example system: Paxos/Raft, ZooKeeper, Causal broadcast, DNS/Cassandra.
Use LINE/ARROW for the spectrum, TEXT for labels, DOT for marker points.""",
    },
    "cap_theorem": {
        "category": "big_data",
        "prompt": """Draw the CAP theorem as a triangle with C, A, P at the three vertices.
C = Consistency, A = Availability, P = Partition tolerance.
Show that in a network partition you must choose only two: CP (HBase), AP (Cassandra), CA (single-node DB).
Place example systems near each side/vertex.
Use POLYGON for the triangle, TEXT for labels, DOT for systems, LINE to connect examples.""",
    },
    "kafka_streaming_pipeline": {
        "category": "big_data",
        "prompt": """Draw a Kafka streaming pipeline.
Producers publish events to a Topic. Topic has multiple partitions.
Consumer groups read from partitions. ZooKeeper/KRaft manages metadata.
Show arrows from producers to topic partitions, then to consumers.
Use RECT for producers/consumers/brokers, smaller stacked RECT for partitions,
TEXT for topic names and consumer groups, ARROW for event flow.""",
    },
    "lambda_architecture": {
        "category": "big_data",
        "prompt": """Draw the Lambda architecture for big data processing.
Incoming data splits into Batch Layer (Hadoop/Spark batch jobs -> Batch Views)
and Speed Layer (Storm/Flink stream processing -> Real-time Views).
Serving Layer merges both views for queries.
Show the data flow with arrows. Label latency: batch = high, speed = low.
Use RECT for layers, ARROW for data flow, TEXT for technology examples.""",
    },
    "database_sharding": {
        "category": "big_data",
        "prompt": """Draw database sharding by user_id range.
Original monolithic DB at top. Below, four shards: Shard 1 (user_id 0-249), Shard 2 (250-499),
Shard 3 (500-749), Shard 4 (750-999).
Show a routing layer directing queries to the correct shard.
Use RECT for shards and router, TEXT for shard key ranges, ARROW for query routing.""",
    },
    "data_lake_layers": {
        "category": "big_data",
        "prompt": """Draw a data lake architecture with bronze, silver, gold layers.
Raw data ingests into Bronze (raw). Silver = cleansed/transformed. Gold = aggregated for analytics.
Show arrows between layers. Add consumption endpoints: BI dashboards, ML training, ad-hoc queries.
Use three stacked horizontal bands (RECT) for layers, ARROW for flow, TEXT for layer descriptions.""",
    },
    "consistent_hashing": {
        "category": "big_data",
        "prompt": """Draw consistent hashing with a circular hash ring.
Hash ring is a CIRCLE. Place nodes A, B, C on the ring. Show keys 1-8 placed on the ring by hash value.
Show that adding node D only remaps keys between C and D, not all keys.
Use CIRCLE for the ring, DOT for nodes and keys, TEXT for labels. Use ARROW to show key migration.""",
    },
}


def call_ollama(prompt, model="glm-5.2:cloud", system=None, max_tokens=8192):
    """Call Ollama API and return the generated text."""
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.5,
        }
    }
    if system:
        payload["system"] = system

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    def _do_request():
        with urllib.request.urlopen(req, timeout=240) as resp:
            return json.loads(resp.read().decode())

    try:
        result = _do_request()
        response = result.get("response", "")
        # Retry once if empty (thinking model may have produced reasoning only)
        if not response.strip():
            result = _do_request()
            response = result.get("response", "")
        return response
    except Exception as e:
        print(f"  Ollama error: {e}")
        return None


def clean_output(text):
    """Extract [DRAW]...[/DRAW] block from model output."""
    # Find the DRAW block
    m = re.search(r'\[DRAW\](.*?)\[/DRAW\]', text, re.DOTALL)
    if m:
        return f"[DRAW]{m.group(1)}[/DRAW]"
    # If no block found, try wrapping the whole thing
    if '[DRAW]' not in text:
        return f"[DRAW]\n{text}\n[/DRAW]"
    return text.strip()


def generate_one(topic_key, model="glm-5.2:cloud", output_dir=None):
    """Generate one diagram for a topic."""
    topic = TOPICS.get(topic_key)
    if not topic:
        print(f"Unknown topic: {topic_key}")
        return None

    print(f"  Generating: {topic_key} ({topic['category']})")

    full_prompt = topic['prompt']

    result = call_ollama(full_prompt, model=model, system=SYSTEM_PROMPT, max_tokens=8192)

    if not result:
        print(f"    FAILED")
        return None

    text = clean_output(result)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, f"{topic_key}.txt")
        with open(out_path, 'w') as f:
            f.write(f"~~{topic_key.replace('_', ' ').title()}~~\n\n{text}")
        print(f"    Saved ({len(text)} chars)")

    return text


def generate_category(category, model="glm-5.2:cloud", output_dir=None, count=None):
    """Generate all topics in a category."""
    topics = [(k, v) for k, v in TOPICS.items() if v['category'] == category]
    if count:
        topics = topics[:count]

    results = {}
    for i, (key, _) in enumerate(topics):
        print(f"\n[{i+1}/{len(topics)}]")
        text = generate_one(key, model=model, output_dir=output_dir)
        results[key] = text
        if i < len(topics) - 1:
            time.sleep(1)
    return results


def generate_all(model="glm-5.2:cloud", output_dir=None, count=None):
    """Generate all topics across all categories."""
    topics = list(TOPICS.items())
    if count:
        topics = topics[:count]

    results = {}
    for i, (key, _) in enumerate(topics):
        print(f"\n[{i+1}/{len(topics)}]")
        text = generate_one(key, model=model, output_dir=output_dir)
        results[key] = text
        if i < len(topics) - 1:
            time.sleep(1)
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate DRAW dataset using Ollama')
    parser.add_argument('--topic', type=str, help='Single topic key')
    parser.add_argument('--category', type=str, help='Generate all topics in a category')
    parser.add_argument('--all', action='store_true', help='Generate ALL topics')
    parser.add_argument('--count', type=int, help='Limit number of topics')
    parser.add_argument('--model', type=str, default='glm-5.2:cloud')
    parser.add_argument('--output-dir', type=str, default='datasets/draw_generated')
    parser.add_argument('--list-categories', action='store_true')
    parser.add_argument('--list-topics', action='store_true')

    args = parser.parse_args()

    if args.list_categories:
        cats = sorted(set(v['category'] for v in TOPICS.values()))
        print("Categories:")
        for c in cats:
            count = sum(1 for v in TOPICS.values() if v['category'] == c)
            print(f"  {c}: {count} topics")
        sys.exit(0)

    if args.list_topics:
        for k in sorted(TOPICS.keys()):
            print(f"  {k}: {TOPICS[k]['category']}")
        sys.exit(0)

    if args.topic:
        generate_one(args.topic, model=args.model, output_dir=args.output_dir)
    elif args.category:
        generate_category(args.category, model=args.model, output_dir=args.output_dir, count=args.count)
    elif args.all:
        generate_all(model=args.model, output_dir=args.output_dir, count=args.count)
    else:
        parser.print_help()
