"""
Ollama-powered content generator for mathwriter datasets.

Generates teaching content for CS algorithms and data structures
in the mathwriter markup format, including hand-drawn diagrams.

Usage:
    python generate_dataset.py --topic dp --count 5
    python generate_dataset.py --all --count 3
"""

import json, os, sys, subprocess, argparse, time, re
from pathlib import Path

HERE = Path(__file__).parent

# ─── Prompt templates ───────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert computer science educator who creates beautiful handwritten-style
teaching materials. You output content in a special markup format that renders as
handwritten pages with diagrams.

## Markup Reference

### Text formatting
- `~~Title~~` — underlined header (must be on its own line)
- `[B]text[/B]` — boxed answer
- `[X]text[/X]` — strikethrough (fake mistake correction)

### Math notation
- `[F]num|den[/F]` — fraction (e.g. `[F]1|2[/F]` = 1/2)
- `[M]a,b;c,d[/M]` — matrix (rows separated by `;`, cells by `,`)
- `[S]lower|upper[/S]` — sum with limits (e.g. `[S]i=1|n[/S]`)
- `[R]content[/R]` — square root
- `[U]content[/U]` — superscript
- `[D]content[/D]` — subscript
- `[V]text[/V]` — vector arrow above
- `[H]text[/H]` — hat above

### Special characters (use directly, no tag needed)
- Arrows: → (or ->)
- Greek: α β γ θ λ π Σ
- Math: ∞ ∈ ∉ ⊂ ⊆ ∪ ∩ ∀ ∃ √ ≠ ≤ ≥
- Subscripts: ₀₁₂₃₄₅₆₇₈₉ ᵢⱼₙ
- Superscripts: ⁰¹²³⁴⁵⁶⁷⁸⁹ ⁱⁿ

### Diagrams (use [G] tag with JSON)
Diagrams are block-level — they start on a new line.

**Array:**
[G]{"type": "array", "values": ["0", "1", "1", "2", "3", "5"], "indices": ["0", "1", "2", "3", "4", "5"]}[/G]

**DP Table (2D grid):**
[G]{"type": "dp_table", "rows": [["", "A", "B"], ["", "0", "1"], ["A", "1", "1"]], "row_labels": ["", "A"], "col_labels": ["", "A", "B"]}[/G]

**Binary Tree:**
[G]{"type": "tree", "nodes": "5:3:8\\n3:1:4\\n8:7:9\\n1:_:_\\n4:_:_\\n7:_:_\\n9:_:_"}[/G]
Format: each line is "value:left_child:right_child". Use `_` for null children. Root is first line.

**Linked List:**
[G]{"type": "linked_list", "values": ["A", "B", "C", "null"]}[/G]

**Graph (weighted directed):**
[G]{"type": "graph", "nodes": [["A", 100, 80], ["B", 200, 40], ["C", 200, 120], ["D", 300, 80]], "edges": [["A", "B", "3"], ["A", "C", "5"], ["B", "D", "2"], ["C", "D", "1"]]}[/G]
Nodes: [label, x, y]. Edges: [from, to, weight]. Position nodes with ~100px spacing.

**Stack:**
[G]{"type": "stack", "items": ["5", "3", "8"]}[/G]

**Queue:**
[G]{"type": "queue", "items": ["A", "B", "C"]}[/G]

**Memory Layout:**
[G]{"type": "memory", "variables": [["x", "5", "0x1000"], ["p", "0x2000", "0x1008"]]}[/G]
Each variable: [name, value, address]

## Rules
1. Output ONLY the markup content — no explanations, no markdown fences.
2. Use blank lines between paragraphs.
3. Every diagram must be on its own line with [G]...[/G].
4. Keep diagrams simple and clear — max 7-8 nodes for trees, max 5x5 for tables.
5. Use proper math notation with the tags above.
6. Make content pedagogically sound — explain the intuition, show the recurrence, walk through an example.
7. Include at least one worked example with step-by-step values.
8. End with a boxed summary of key takeaways.
"""

TOPIC_PROMPTS = {
    "dp_fibonacci": """Create a 1-page teaching note about computing Fibonacci numbers with dynamic programming.

Include:
1. Title: "Fibonacci with Dynamic Programming"
2. Definition: Fib(0)=0, Fib(1)=1, Fib(n)=Fib(n-1)+Fib(n-2)
3. An array diagram showing the first 7 Fibonacci numbers with indices
4. Explanation of the recurrence
5. A DP table showing how each value is computed from previous two
6. Time/space complexity
7. Boxed key insight: "DP replaces recursion by storing subproblem results"

Make it feel like handwritten lecture notes — natural, slightly informal, with clear structure.""",

    "dp_knapsack": """Create a 1-page teaching note about the 0/1 Knapsack problem with dynamic programming.

Include:
1. Title: "0/1 Knapsack — Dynamic Programming"
2. Problem statement: n items with weights wᵢ and values vᵢ, capacity W
3. DP definition: dp[i][j] = max value using first i items with capacity j
4. A small example: items [(weight=2,value=3), (3,4), (4,5), (5,6)], W=8
5. A DP table diagram (5 rows × 9 columns) showing the filled values
6. The recurrence: dp[i][j] = max(dp[i-1][j], dp[i-1][j-wᵢ] + vᵢ)
7. Trace through one cell computation
8. Boxed key insight about the choice at each step""",

    "dp_lcs": """Create a 1-page teaching note about Longest Common Subsequence (LCS) with DP.

Include:
1. Title: "Longest Common Subsequence"
2. Definition with example strings: X="ABCBDAB", Y="BDCABA"
3. DP recurrence: if xᵢ=yⱼ then 1+dp[i-1][j-1] else max(dp[i-1][j], dp[i][j-1])
4. A DP table diagram for the example (at least 5×5)
5. Show how to read back the LCS from the table
6. Arrows in the DP table showing the backtracking path
7. Boxed summary""",

    "dp_edit_distance": """Create a 1-page teaching note about Edit Distance (Levenshtein) with DP.

Include:
1. Title: "Edit Distance — Levenshtein Distance"
2. Definition: min operations (insert, delete, substitute) to convert string A to B
3. Example: "kitten" → "sitting"
4. DP recurrence with all three operations
5. A DP table diagram for the example
6. Show the edit sequence
7. Boxed key insight""",

    "tree_traversals": """Create a 1-page teaching note about binary tree traversals.

Include:
1. Title: "Binary Tree Traversals"
2. A binary tree diagram with 7 nodes (values 1-7 in a balanced BST)
3. Inorder traversal: definition + result for the example tree
4. Preorder traversal: definition + result
5. Postorder traversal: definition + result
6. Level-order (BFS): definition + result
7. A small table comparing all four orders
8. Boxed mnemonic for remembering the orders""",

    "tree_bst": """Create a 1-page teaching note about Binary Search Trees.

Include:
1. Title: "Binary Search Trees (BST)"
2. BST property: left < root < right
3. A BST diagram with 7 nodes
4. Search operation walkthrough
5. Insert operation with before/after diagrams
6. Three cases for deletion (leaf, one child, two children)
7. Time complexity: O(h) where h is height
8. Boxed: "Balanced BST → O(log n), Degenerate → O(n)\"""",

    "graph_bfs": """Create a 1-page teaching note about Breadth-First Search (BFS).

Include:
1. Title: "Breadth-First Search (BFS)"
2. A graph diagram with 6 nodes and directed edges
3. Queue-based algorithm steps
4. Show the queue state at each step for the example graph
5. BFS tree / levels diagram
6. Applications: shortest path (unweighted), level order
7. Time complexity: O(V+E)
8. Boxed: "BFS explores level by level — use a queue\"""",

    "graph_dfs": """Create a 1-page teaching note about Depth-First Search (DFS).

Include:
1. Title: "Depth-First Search (DFS)"
2. A graph diagram with 6 nodes
3. Recursive algorithm
4. Discovery/finish times on the example
5. Edge classification: tree, back, forward, cross
6. Applications: cycle detection, topological sort, SCCs
7. Time complexity: O(V+E)
8. Boxed: "DFS goes deep first — use recursion or explicit stack\"""",

    "graph_dijkstra": """Create a 1-page teaching note about Dijkstra's shortest path algorithm.

Include:
1. Title: "Dijkstra's Algorithm"
2. A weighted graph diagram with 5 nodes
3. Algorithm steps with priority queue
4. Distance table showing updates at each step
5. Trace through the example
6. Final shortest paths from source
7. Limitation: no negative weights
8. Boxed: "Greedy + Relaxation = Optimal for non-negative weights\"""",

    "linked_list": """Create a 1-page teaching note about Linked Lists.

Include:
1. Title: "Linked Lists"
2. A linked list diagram with 4 nodes
3. Node structure: data + next pointer
4. Insert at head operation with before/after diagrams
5. Delete operation
6. Comparison with arrays (pros/cons table)
7. Time complexity table for operations
8. Boxed: "Linked lists = dynamic size, O(1) insert/delete at head\"""",

    "stack_queue": """Create a 1-page teaching note about Stacks and Queues.

Include:
1. Title: "Stacks and Queues"
2. Stack diagram (LIFO) with push/pop operations
3. Queue diagram (FIFO) with enqueue/dequeue operations
4. Comparison table
5. Applications: function calls (stack), BFS (queue), undo (stack)
6. Implementation: array-based vs linked-list-based
7. Time complexity table
8. Boxed: "Stack = LIFO (plate stack), Queue = FIFO (line)\"""",

    "sorting": """Create a 1-page teaching note about sorting algorithms comparison.

Include:
1. Title: "Sorting Algorithms"
2. Array diagram showing unsorted → sorted
3. Quick overview of: Bubble, Selection, Insertion, Merge, Quick
4. Comparison table: best/average/worst time, space, stable?
5. When to use which
6. Boxed: "Merge Sort = guaranteed O(n log n), Quick Sort = fastest in practice\"""",

    "hashing": """Create a 1-page teaching note about Hash Tables.

Include:
1. Title: "Hash Tables"
2. Hash function concept diagram
3. Collision resolution: chaining diagram
4. Array of buckets with linked lists
5. Operations: insert, search, delete — O(1) average
6. Load factor and rehashing
7. Comparison with arrays and BSTs
8. Boxed: "Hash tables = O(1) average, but worst-case O(n)\"""",

    "pointers_memory": """Create a 1-page teaching note about Pointers and Memory.

Include:
1. Title: "Pointers and Memory Layout"
2. Memory layout diagram with stack and heap
3. Pointer declaration and dereferencing
4. Example: int x=5, int *p=&x
5. Memory diagram showing addresses and values
6. Pointer arithmetic
7. Common pitfalls: null pointers, dangling pointers
8. Boxed: "A pointer stores an address — think of it as an arrow\"""",

    "recursion": """Create a 1-page teaching note about Recursion.

Include:
1. Title: "Recursion"
2. Factorial example with recursion tree diagram
3. Base case + recursive case structure
4. Call stack visualization for factorial(4)
5. Fibonacci: naive recursion tree showing repeated work
6. Tail recursion concept
7. When to use recursion vs iteration
8. Boxed: "Every recursive solution needs a base case\"""",
}


def call_ollama(prompt, model="glm-5.2:cloud", system=None, max_tokens=4096):
    """Call Ollama API and return the generated text."""
    import urllib.request, urllib.error

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.7,
        }
    }
    if system:
        payload["system"] = system

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode())
            response = result.get("response", "")
            # If response is empty but thinking exists, the model used all tokens for thinking.
            # Retry with higher num_predict.
            if not response.strip() and result.get("thinking"):
                print(f"  Model used all tokens for thinking. Retrying with 2x tokens...")
                payload["options"]["num_predict"] = max_tokens * 2
                data2 = json.dumps(payload).encode('utf-8')
                req2 = urllib.request.Request(url, data=data2, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req2, timeout=180) as resp2:
                    result2 = json.loads(resp2.read().decode())
                    response = result2.get("response", "")
            return response
    except urllib.error.URLError as e:
        print(f"  Ollama error: {e}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def clean_output(text):
    """Clean up model output — remove markdown fences, fix common issues."""
    # Remove markdown code fences
    text = re.sub(r'^```\w*\s*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n```\s*$', '', text, flags=re.MULTILINE)

    # Remove leading/trailing whitespace
    text = text.strip()

    # Fix common Ollama artifacts
    text = text.replace('\\n', '\n')

    return text


def generate_one(topic_key, model="glm-5.2:cloud", output_dir=None):
    """Generate one teaching note for a topic."""
    prompt = TOPIC_PROMPTS.get(topic_key)
    if not prompt:
        print(f"Unknown topic: {topic_key}")
        return None

    print(f"\n{'='*60}")
    print(f"Generating: {topic_key}")
    print(f"{'='*60}")

    full_prompt = f"{SYSTEM_PROMPT}\n\n---\n\n{prompt}"

    result = call_ollama(full_prompt, model=model, system=None, max_tokens=4096)

    if not result:
        print(f"  FAILED to generate {topic_key}")
        return None

    text = clean_output(result)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, f"{topic_key}.txt")
        with open(out_path, 'w') as f:
            f.write(text)
        print(f"  Saved to {out_path} ({len(text)} chars)")

    return text


def generate_all(model="glm-5.2:cloud", output_dir=None, count=None):
    """Generate all topics."""
    topics = list(TOPIC_PROMPTS.keys())
    if count:
        topics = topics[:count]

    results = {}
    for i, topic in enumerate(topics):
        print(f"\n[{i+1}/{len(topics)}] {topic}")
        text = generate_one(topic, model=model, output_dir=output_dir)
        results[topic] = text
        if i < len(topics) - 1:
            time.sleep(2)  # Brief pause between generations

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate mathwriter dataset using Ollama')
    parser.add_argument('--topic', type=str, help='Single topic key to generate')
    parser.add_argument('--all', action='store_true', help='Generate all topics')
    parser.add_argument('--count', type=int, help='Number of topics to generate')
    parser.add_argument('--model', type=str, default='glm-5.2:cloud', help='Ollama model name')
    parser.add_argument('--output-dir', type=str, default='datasets/generated',
                        help='Output directory for generated files')
    parser.add_argument('--list-topics', action='store_true', help='List available topics')

    args = parser.parse_args()

    if args.list_topics:
        print("Available topics:")
        for k in sorted(TOPIC_PROMPTS.keys()):
            print(f"  {k}")
        sys.exit(0)

    if args.topic:
        generate_one(args.topic, model=args.model, output_dir=args.output_dir)
    elif args.all:
        generate_all(model=args.model, output_dir=args.output_dir, count=args.count)
    else:
        parser.print_help()
