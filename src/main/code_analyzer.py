import ast
import os
from collections import defaultdict
import openai
from typing import Dict, List, Set, Tuple
import uuid
import langchain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
import dotenv
import time
from graphviz import Digraph
# Load environment variables
dotenv.load_dotenv()

class FunctionNode:
    """Represents a node in the function call tree."""
    def __init__(self, name: str, file_path: str, source: str):
        self.name = name
        self.file_path = file_path
        self.source = source
        self.children: List[FunctionNode] = []
        self.callers: Set[str] = set()

# Azure OpenAI Configuration
AZURE_CONFIG = {
    "api_version": "2024-08-01-preview",
    "azure_endpoint": "https://ai-akshaopenai.azure.com/openai/deployments/gpt-4o/chat/completions?2024-08-01-preview",
    "api_key": os.getenv("OPENAI_KEY")  # Load API key from environment variable
}

from graphviz import Digraph


from graphviz import Digraph

def build_call_graph(function_nodes):
    """
    Builds a call graph dictionary from function_nodes.
    
    Args:
        function_nodes (dict): Mapping from function name to function node object.
        
    Returns:
        dict: A call graph {function_name: [list of callee function names]}
    """
    call_graph = {}
    for func_name, node in function_nodes.items():
        callees = [f"{c.name}" for c in node.children]  # You can include file if needed
        call_graph[func_name] = callees
    return call_graph

def draw_function_call_tree(call_graph, output_path='function_call_tree', file_format='png'):
    """
    Draws a function call tree from a call graph dictionary.
    """
    dot = Digraph(comment='Function Call Tree')
    dot.attr('node', shape='box', style='filled', color='lightblue')

    # Add nodes and edges
    for caller, callees in call_graph.items():
        dot.node(caller)
        for callee in callees:
            dot.node(callee)
            dot.edge(caller, callee)

    # Render and save
    dot.render(output_path, format=file_format, view=True)
    print(f"Function call tree saved to {output_path}.{file_format}")


from anytree import Node, RenderTree

def build_function_tree(function_nodes):
    """
    Builds a tree based on function call relationships using anytree.
    """
    node_map = {}

    # Create all nodes with unique labels: file_path:function_name
    for func_name, fn_node in function_nodes.items():
        label = f"{fn_node.file_path}:{func_name}"
        node_map[func_name] = Node(label)

    # Set up parent-child relationships
    for func_name, fn_node in function_nodes.items():
        parent = node_map[func_name]
        for child_node in fn_node.children:
            child_label = f"{child_node.file_path}:{child_node.name}"
            child = node_map.get(child_node.name)
            if child:
                child.parent = parent  # assign parent-child relation

    # Find root nodes (those without parents)
    roots = [n for n in node_map.values() if n.is_root]
    
    # Print the tree(s)
    for root in roots:
        for pre, fill, node in RenderTree(root):
            print(f"{pre}{node.name}")




class CodeAnalyzer:
    """Main class for analyzing Python codebases with debugging."""
    
    def __init__(self, project_path: str, main_file: str, config):
        self.project_path = project_path
        self.main_file = os.path.join(project_path, main_file)
        self.function_nodes: Dict[str, FunctionNode] = {}
        self.imports: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        self.api_version = config.get("api_version")
        self.azure_endpoint = config.get("azure_endpoint")
        self.api_key = config.get("api_key")
        self.client = self._setup_client()
        print(f"Initialized CodeAnalyzer for project: {project_path}, main file: {main_file}")


    def visualize_call_tree(self, output_file="call_tree"):
        dot = Digraph(comment="Function Call Tree")

        # Add nodes
        for func_name, node in self.function_nodes.items():
            dot.node(func_name, label=node.name)

            # Add edges from caller to callee
            for child in node.children:
                dot.edge(func_name, f"{child.file_path}:{child.name}")

        dot.render(output_file, format='png', cleanup=True)
        print(f"Call tree saved as {output_file}.png")

    def _setup_client(self) -> openai.AzureOpenAI:
        """Set up and return the Azure OpenAI client."""
        print("Setting up Azure OpenAI client...")
        client = openai.AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint
        )
        print("Azure OpenAI client setup complete.")
        return client
        
    def analyze_project(self) -> None:
        """Analyze all Python files in the project directory."""
        print(f"Starting project analysis for: {self.project_path}")
        if not os.path.exists(self.main_file):
            raise FileNotFoundError(f"Main file {self.main_file} not found")
            
        # Process all Python files
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    print(f"\nProcessing file: {file_path}")
                    time.sleep(5)  # Simulate processing delay for clarity
                    self._analyze_file(file_path)
                    
        # Build function call tree
        print("\nStarting to build function call tree...")
        self._build_call_tree()
        # self.visualize_call_tree("my_call_tree")

        print("Function call tree construction complete.")
        self._print_tree_summary()
        # USAGE
        # call_graph = build_call_graph(self.function_nodes)
        # draw_function_call_tree(call_graph)
        build_function_tree(self.function_nodes)
        exit('DONE')
        
    def _analyze_file(self, file_path: str) -> None:
        """Analyze a single Python file for functions and calls."""
        print(f"Analyzing file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
            
        # try:
        tree = ast.parse(source)
        print(f"AST parsed successfully for {file_path}")
        # except SyntaxError:
        #     print(f"Warning: Could not parse {file_path}")
        #     return
            
        # Extract functions and calls
        num_functions = 0
        for node in ast.walk(tree):
            print(f"num_functions : {num_functions}")
            
            if isinstance(node, ast.FunctionDef):
                func_name = f"{file_path}:{node.name}"
                func_source = ast.get_source_segment(source, node)
                print(f"Found func_source: {func_source}")
                print('$$$$$$$$$$$$$$$$$$$$$$$$$$$')
                print('$$$$$$$$$$$$$$$$$$$$$$$$$$$')
                print(f"num_functions : {num_functions}")
                print('$$$$$$$$$$$$$$$$$$$$$$$$$$$')
                print('$$$$$$$$$$$$$$$$$$$$$$$$$$$')
                
                self.function_nodes[func_name] = FunctionNode(
                    node.name, file_path, func_source
                )
                print(f"Function node created: {func_name}")
                print(f"Function node source: {func_source}")
                print(f"Function node file_path: {file_path}")
                print(f"Function node name: {node.name}")
                print(f"Function node: {self.function_nodes[func_name]}")
                print(f"Function node source: {self.function_nodes[func_name].source}")
                print(f"Function node file_path: {self.function_nodes[func_name].file_path}")
                print(f"Function node name: {self.function_nodes[func_name].name}")
                print(f"Function node children: {self.function_nodes[func_name].children}")
                print(f"Function node callers: {self.function_nodes[func_name].callers}")
                print(self.function_nodes)
                print(f"Added function node: {func_name}")
                
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                self._process_imports(node, file_path)
                print(f"Processed imports for {file_path}")
            num_functions += 1
        # Extract function calls
        visitor = FunctionCallVisitor(self.function_nodes, file_path)
        print(visitor)
        visitor.visit(tree)
        self.function_nodes.update(visitor.function_nodes)
        print(visitor.__dict__)  # Shows all instance attributes
        print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
        print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
        print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
        print(f"Function node children: {self.function_nodes[func_name].children}")
        print(f"Function node callers: {self.function_nodes[func_name].callers}")
        print(f"Function calls analyzed for {file_path}. Total nodes: {len(self.function_nodes)}")
    def _process_imports(self, node: ast.AST, file_path: str) -> None:
        """Process import statements."""
        if isinstance(node, ast.Import):
            for alias in node.names:
                self.imports[file_path].append((alias.name, alias.asname or alias.name))
                print(f"Import added: {alias.name} in {file_path}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module
            for alias in node.names:
                self.imports[file_path].append((
                    f"{module}.{alias.name}",
                    alias.asname or alias.name
                ))
                print(f"ImportFrom added: {module}.{alias.name} in {file_path}")
                
    def _build_call_tree(self) -> None:
        """Construct the function call tree starting from main file."""
        print("\nBuilding function call tree...")
        visited = set()
        
        def build_from_function(func_name: str, depth: int = 0) -> None:
            indent = "  " * depth
            if func_name in visited or func_name not in self.function_nodes:
                print(f"{indent}Skipping {func_name} (visited or not found)")
                return
                
            visited.add(func_name)
            node = self.function_nodes[func_name]
            print(f"{indent}Processing function: {func_name}")
            
            # Find all calls from this function
            with open(node.file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
                print(f"{indent}  Parsed AST for {node.file_path}")
                
            visitor = FunctionCallVisitor(self.function_nodes, node.file_path)
            visitor.current_function = func_name
            visitor.visit(tree)
            
            # Add children
            for called_func in visitor.called_functions:
                if called_func in self.function_nodes:
                    node.children.append(self.function_nodes[called_func])
                    self.function_nodes[called_func].callers.add(func_name)
                    print(f"{indent}  Added child: {called_func} to {func_name}")
                    print(f"{indent}  Updated callers for {called_func}: {self.function_nodes[called_func].callers}")
                    
            # Recursively build for children
            for child in node.children:
                print(f"{indent}  Recursing into child: {child.file_path}:{child.name}")
                build_from_function(f"{child.file_path}:{child.name}", depth + 1)
                
        # Start from main file's top-level functions
        print(f"Starting tree build from main file: {self.main_file}")
        with open(self.main_file, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = f"{self.main_file}:{node.name}"
                print(f"\nStarting tree construction for top-level function: {func_name}")
                build_from_function(func_name)
    
    def _print_tree_summary(self) -> None:
        """Print a summary of the function call tree."""
        print("\n=== Function Call Tree Summary ===")
        for func_name, node in self.function_nodes.items():
            
            print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
            print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
            print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
            print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
            print(f"\nFunction: {func_name}")
            print(f"  File: {node.file_path}")
            print(f"  Callers: {', '.join(node.callers) or 'None'}")
            print(f"  children ==> Callees: {', '.join(f'{c.file_path}:{c.name}' for c in node.children) or 'None'}")
            # print(f"  Source preview: {node.source[:100].replace('\n', ' ')}...")
            print("  Source preview: {}...".format(node.source[:100].replace('\n', ' ')))

        print("=================================")
    def query_codebase(self, query: str) -> str:
        """Process a natural language query about the codebase."""
        print(f"\nProcessing query: {query}")
        # Get relevant context
        context = self._get_query_context(query)
        print(f"Query context:\n{context}")
        
        # Create prompt
        prompt_template = PromptTemplate(
            input_variables=["context", "query"],
            template="""
            You are a code analysis assistant. Based on the following context about a Python codebase,
            answer the query as accurately and concisely as possible.

            Context:
            {context}

            Query:
            {query}

            Answer:
            """
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": query}
            ],
            temperature=0,
            max_tokens=10000
        )
        answer = response.choices[0].message.content
        print(f"Query response: {answer}")
        return answer
        
    def _get_query_context(self, query: str) -> str:
        """Extract relevant context for a query."""
        print(f"Extracting context for query: {query}")
        context = []
        
        # Simple keyword-based context selection
        for func_name, node in self.function_nodes.items():
            if any(keyword in func_name.lower() or keyword in node.source.lower()
                  for keyword in query.lower().split()):
                context.append(f"Function: {func_name}\nSource:\n{node.source}\n")
                context.append(f"Callers: {', '.join(node.callers) or 'None'}\n")
                context.append(f"Callees: {', '.join(c.name for c in node.children) or 'None'}\n")
                print(f"Added context for function: {func_name}")
                
        return "\n".join(context) if context else "No relevant context found."

class FunctionCallVisitor(ast.NodeVisitor):
    """AST visitor to identify function calls."""
    
    def __init__(self, function_nodes: Dict[str, FunctionNode], file_path: str):
        self.function_nodes = function_nodes
        self.file_path = file_path
        self.current_function = None
        self.called_functions: Set[str] = set()
        print(f"Initialized FunctionCallVisitor for {file_path}")
        
    def visit_Call(self, node: ast.Call) -> None:
        """Process function call nodes."""
        if isinstance(node.func, ast.Name):
            func_name = f"{self.file_path}:{node.func.id}"
            if self.current_function and func_name in self.function_nodes:
                self.called_functions.add(func_name)
                print(f"Detected call to {func_name} from {self.current_function}")
                
        elif isinstance(node.func, ast.Attribute):
            # Handle method calls (simplified)
            if isinstance(node.func.value, ast.Name):
                possible_func = f"{self.file_path}:{node.func.attr}"
                if self.current_function and possible_func in self.function_nodes:
                    self.called_functions.add(possible_func)
                    print(f"Detected method call to {possible_func} from {self.current_function}")
                    
        self.generic_visit(node)

def main():
    """Main function to demonstrate usage."""
    print("Starting CodeAnalyzer demonstration...")
    analyzer = CodeAnalyzer("/home/ntlpt19/personal_projects/deep_code_block_builder/src/data", "model.py", AZURE_CONFIG)
    try:
        analyzer.analyze_project()
        # Example queries
        queries = [
            "What does the main function do?",
            "Which functions call the process_data function?",
            "Describe the execution flow starting from main"
        ]
        
        for query in queries:
            print(f"\nExecuting query: {query}")
            print(f"Answer: {analyzer.query_codebase(query)}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()