"""
Generate rich image-mode [G] datasets for logic gates, relational models,
and big data systems. These use the fixed diagram builders in diagrams_extra.py.
"""
import json, os, textwrap

OUT_DIR = "datasets/generated"
os.makedirs(OUT_DIR, exist_ok=True)


def write(name, title, body):
    path = os.path.join(OUT_DIR, f"{name}.txt")
    with open(path, "w") as f:
        f.write(f"~~{title}~~\n\n{body}\n")
    print(f"wrote {path}")


def gate_truth_table(gate):
    if gate == 'NOT':
        return [["A", "Y"], ["0", "1"], ["1", "0"]]
    base = [["A", "B", "Y"]]
    rows = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for a, b in rows:
        if gate in ("AND", "NAND"):
            y = int(a and b)
        elif gate in ("OR", "NOR"):
            y = int(a or b)
        elif gate == "XOR":
            y = int(a ^ b)
        else:
            y = int(a and b)
        if gate in ("NAND", "NOR"):
            y = 1 - y
        base.append([str(a), str(b), str(y)])
    return base


# ═══════════════════════════════════════════════════════════════════════
#  Logic gates
# ═══════════════════════════════════════════════════════════════════════
for gate in ["AND", "OR", "NOT", "XOR", "NAND", "NOR"]:
    inputs = ["A"] if gate == "NOT" else ["A", "B"]
    spec = {
        "type": "logic_gate",
        "gate": gate,
        "inputs": inputs,
        "output": "Y",
        "truth_table": gate_truth_table(gate),
    }
    body = f"The {gate} gate.\n\n[G]{json.dumps(spec)}[/G]\n\n"
    if gate == "AND":
        body += "Output Y is 1 only when all inputs are 1."
    elif gate == "OR":
        body += "Output Y is 1 when at least one input is 1."
    elif gate == "NOT":
        body += "Output Y is the inverse of the input."
    elif gate == "XOR":
        body += "Output Y is 1 when the inputs differ."
    elif gate == "NAND":
        body += "Output Y is 0 only when all inputs are 1."
    elif gate == "NOR":
        body += "Output Y is 1 only when no input is 1."
    write(f"logic_gate_{gate.lower()}", f"{gate} Gate", body)


# Half adder circuit
half_adder = {
    "type": "logic_circuit",
    "inputs": [
        {"label": "A", "x": 50, "y": 80},
        {"label": "B", "x": 50, "y": 160},
    ],
    "gates": [
        {"type": "XOR", "x": 180, "y": 90, "label": "XOR"},
        {"type": "AND", "x": 180, "y": 160, "label": "AND"},
    ],
    "wires": [
        ("A", "XOR"),
        ("A", "AND"),
        ("B", "XOR"),
        ("B", "AND"),
    ],
    "outputs": [
        {"label": "Sum", "x": 320, "y": 100},
        {"label": "Carry", "x": 320, "y": 175},
    ],
}
write(
    "logic_half_adder",
    "Half Adder",
    f"A half adder adds two single bits and produces Sum and Carry.\n\n[G]{json.dumps(half_adder)}[/G]",
)


# Full adder circuit
full_adder = {
    "type": "logic_circuit",
    "inputs": [
        {"label": "A", "x": 40, "y": 60},
        {"label": "B", "x": 40, "y": 120},
        {"label": "Cin", "x": 40, "y": 180},
    ],
    "gates": [
        {"type": "XOR", "x": 160, "y": 75, "label": "X1"},
        {"type": "XOR", "x": 300, "y": 95, "label": "X2"},
        {"type": "AND", "x": 160, "y": 145, "label": "A1"},
        {"type": "AND", "x": 300, "y": 165, "label": "A2"},
        {"type": "OR", "x": 430, "y": 155, "label": "OR"},
    ],
    "wires": [
        ("A", "X1"),
        ("B", "X1"),
        ("A", "A1"),
        ("B", "A1"),
        ("X1", "X2"),
        ("Cin", "X2"),
        ("X1", "A2"),
        ("Cin", "A2"),
        ("A1", "OR"),
        ("A2", "OR"),
    ],
    "outputs": [
        {"label": "Sum", "x": 430, "y": 95},
        {"label": "Cout", "x": 530, "y": 155},
    ],
}
write(
    "logic_full_adder",
    "Full Adder",
    f"A full adder adds three bits (A, B, Cin) and produces Sum and Cout.\n\n[G]{json.dumps(full_adder)}[/G]",
)


# SR latch
sr_latch = {
    "type": "logic_circuit",
    "inputs": [
        {"label": "S", "x": 40, "y": 80},
        {"label": "R", "x": 40, "y": 200},
    ],
    "gates": [
        {"type": "NOR", "x": 160, "y": 70, "label": "NOR1"},
        {"type": "NOR", "x": 160, "y": 190, "label": "NOR2"},
    ],
    "wires": [
        ("S", "NOR1"),
        ("R", "NOR2"),
        ("NOR1", "NOR2"),
        ("NOR2", "NOR1"),
    ],
    "outputs": [
        {"label": "Q", "x": 300, "y": 85},
        {"label": "Q'", "x": 300, "y": 205},
    ],
}
write(
    "logic_sr_latch",
    "SR Latch",
    f"An SR latch built from two cross-coupled NOR gates.\n\n[G]{json.dumps(sr_latch)}[/G]",
)


# ═══════════════════════════════════════════════════════════════════════
#  Relational models
# ═══════════════════════════════════════════════════════════════════════

university_er = {
    "type": "er_diagram",
    "entities": [
        {"name": "Student", "attrs": ["student_id PK", "name"], "x": 60, "y": 90},
        {"name": "Course", "attrs": ["course_id PK", "title"], "x": 320, "y": 90},
        {"name": "Professor", "attrs": ["prof_id PK", "name"], "x": 540, "y": 90},
    ],
    "relationships": [
        {"name": "Enrolls", "from": "Student", "to": "Course", "card": "M:N", "x": 200, "y": 120},
        {"name": "Teaches", "from": "Professor", "to": "Course", "card": "1:N", "x": 440, "y": 120},
    ],
}
write(
    "er_diagram_university",
    "University ER Diagram",
    f"Entity-relationship model for a university.\n\n[G]{json.dumps(university_er)}[/G]",
)


schema = {
    "type": "relational_schema",
    "tables": [
        {"name": "Customers", "cols": ["customer_id PK", "name", "email"], "x": 30, "y": 30},
        {"name": "Orders", "cols": ["order_id PK", "customer_id FK", "order_date"], "x": 220, "y": 30},
        {"name": "Order_Items", "cols": ["item_id PK", "order_id FK", "product_id FK", "qty"], "x": 410, "y": 30},
        {"name": "Products", "cols": ["product_id PK", "name", "price"], "x": 30, "y": 170},
    ],
    "relationships": [
        {"from": ("Customers", "customer_id"), "to": ("Orders", "customer_id"), "card": "1:N"},
        {"from": ("Orders", "order_id"), "to": ("Order_Items", "order_id"), "card": "1:N"},
        {"from": ("Products", "product_id"), "to": ("Order_Items", "product_id"), "card": "1:N"},
    ],
}
write(
    "relational_schema_example",
    "Relational Schema",
    f"E-commerce relational schema with primary and foreign keys.\n\n[G]{json.dumps(schema)}[/G]",
)


normalization = {
    "type": "relational_schema",
    "tables": [
        {"name": "Student_Courses", "cols": ["student_id", "course_id", "course_title", "instructor"], "x": 40, "y": 30},
        {"name": "Students", "cols": ["student_id PK", "student_name"], "x": 40, "y": 160},
        {"name": "Courses", "cols": ["course_id PK", "course_title", "instructor_id FK"], "x": 240, "y": 160},
        {"name": "Instructors", "cols": ["instructor_id PK", "instructor_name"], "x": 440, "y": 160},
    ],
    "relationships": [
        {"from": ("Students", "student_id"), "to": ("Student_Courses", "student_id"), "card": "M:N"},
        {"from": ("Courses", "course_id"), "to": ("Student_Courses", "course_id"), "card": "M:N"},
        {"from": ("Instructors", "instructor_id"), "to": ("Courses", "instructor_id"), "card": "1:N"},
    ],
}
write(
    "normalization_1nf_to_3nf",
    "Database Normalization",
    f"Decomposing a denormalized table into 3NF relations.\n\n[G]{json.dumps(normalization)}[/G]",
)


for join_type in ["INNER", "LEFT", "RIGHT", "FULL"]:
    spec = {"type": "sql_join_venn", "join_type": join_type, "labels": ["Employees", "Departments"]}
    desc = {
        "INNER": "Returns only matching rows from both tables.",
        "LEFT": "Returns all rows from the left table and matching rows from the right.",
        "RIGHT": "Returns all rows from the right table and matching rows from the left.",
        "FULL": "Returns all rows when there is a match in either table.",
    }[join_type]
    write(f"sql_join_{join_type.lower()}", f"{join_type} JOIN", f"{desc}\n\n[G]{json.dumps(spec)}[/G]")


# ═══════════════════════════════════════════════════════════════════════
#  Big data
# ═══════════════════════════════════════════════════════════════════════

mapreduce = {
    "type": "mapreduce",
    "input_splits": ["the cat sat", "cat on mat"],
    "map_output": [
        ["(the,1)", "(cat,1)", "(sat,1)"],
        ["(cat,1)", "(on,1)", "(mat,1)"],
    ],
    "reduce_output": ["cat 2", "mat 2", "the 1", "sat 1"],
}
write(
    "mapreduce_wordcount",
    "MapReduce Word Count",
    f"Counting word frequencies with MapReduce.\n\n[G]{json.dumps(mapreduce)}[/G]",
)


cap = {
    "type": "cap_theorem",
    "corners": {"C": (210, 50), "A": (70, 240), "P": (350, 240)},
    "examples": [
        {"name": "single-node DB", "x": 210, "y": 140, "type": "CA"},
        {"name": "HBase", "x": 110, "y": 200, "type": "CP"},
        {"name": "Cassandra", "x": 310, "y": 200, "type": "AP"},
    ],
}
write(
    "cap_theorem",
    "CAP Theorem",
    f"In a distributed data store you can guarantee at most two of Consistency, Availability, Partition tolerance.\n\n[G]{json.dumps(cap)}[/G]",
)


sharding = {
    "type": "database_sharding",
    "shards": [
        {"name": "Shard 1", "range": "user_id 0-249"},
        {"name": "Shard 2", "range": "user_id 250-499"},
        {"name": "Shard 3", "range": "user_id 500-749"},
    ],
    "routing_key": "user_id",
}
write(
    "database_sharding",
    "Database Sharding",
    f"Distributing rows across shards by a routing key.\n\n[G]{json.dumps(sharding)}[/G]",
)


chash = {
    "type": "consistent_hashing",
    "nodes": [
        {"name": "A", "pos": 0.1},
        {"name": "B", "pos": 0.4},
        {"name": "C", "pos": 0.7},
    ],
    "keys": [
        {"name": "1", "pos": 0.15},
        {"name": "2", "pos": 0.35},
        {"name": "3", "pos": 0.55},
        {"name": "4", "pos": 0.85},
    ],
    "new_node": {"name": "D", "pos": 0.2},
}
write(
    "consistent_hashing",
    "Consistent Hashing",
    f"Mapping keys and nodes on a ring. Adding node D remaps only nearby keys.\n\n[G]{json.dumps(chash)}[/G]",
)


hdfs = {
    "type": "hdfs_architecture",
    "name_node": {"name": "NameNode"},
    "data_nodes": [
        {"name": "DataNode 1", "blocks": ["blk1", "blk2"]},
        {"name": "DataNode 2", "blocks": ["blk2", "blk3"]},
        {"name": "DataNode 3", "blocks": ["blk1", "blk3"]},
    ],
}
write(
    "hdfs_architecture",
    "HDFS Architecture",
    f"HDFS stores files as replicated blocks across DataNodes, managed by the NameNode.\n\n[G]{json.dumps(hdfs)}[/G]",
)


kafka = {
    "type": "kafka_pipeline",
    "producers": ["Producer 1", "Producer 2"],
    "topic": "User Events",
    "consumers": ["Consumer A", "Consumer B"],
}
write(
    "kafka_streaming_pipeline",
    "Kafka Streaming Pipeline",
    f"Producers publish events to a topic; consumers read independently.\n\n[G]{json.dumps(kafka)}[/G]",
)


spark = {
    "type": "spark_lineage",
    "rdds": [
        {"name": "RDD1", "x": 60, "y": 80},
        {"name": "RDD2", "x": 220, "y": 80},
        {"name": "RDD3", "x": 380, "y": 80},
    ],
    "stages": [
        {"name": "Stage 1", "rdds": ["RDD1", "RDD2"]},
        {"name": "Stage 2", "rdds": ["RDD2", "RDD3"]},
    ],
}
write(
    "spark_rdd_lineage",
    "Spark RDD Lineage",
    f"Spark tracks RDD lineage to recompute lost partitions.\n\n[G]{json.dumps(spark)}[/G]",
)

print("done")
