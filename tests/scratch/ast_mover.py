import ast
import astunparse

def move_methods(source_file, target_file, method_names):
    with open(source_file, "r", encoding="utf-8") as f:
        source_code = f.read()

    tree = ast.parse(source_code)
    class_node = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "IQ_Option":
            class_node = node
            break

    if not class_node:
        print(f"Class IQ_Option not found in {source_file}")
        return

    methods_to_move = []
    methods_to_keep = []

    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name in method_names:
            methods_to_move.append(node)
        else:
            methods_to_keep.append(node)

    if not methods_to_move:
        print(f"No methods found to move from {method_names}")
        return

    class_node.body = methods_to_keep

    new_source_code = astunparse.unparse(tree)
    with open(source_file, "w", encoding="utf-8") as f:
        f.write(new_source_code)

    extracted_code = ""
    for method in methods_to_move:
        extracted_code += "\n    " + astunparse.unparse(method).replace("\n", "\n    ").strip() + "\n"

    with open(target_file, "a", encoding="utf-8") as f:
        f.write("\n" + extracted_code)

    print(f"Moved {len(methods_to_move)} methods from {source_file} to {target_file}")

if __name__ == "__main__":
    move_methods(
        "iqoptionapi/stable_api.py", 
        "iqoptionapi/mixins/management_mixin.py", 
        ["get_all_init", "get_all_init_v2", "__get_binary_open", "__get_digital_open", "__get_other_open", "get_all_open_time"]
    )
