import os
import re
import json

import os
import re
import ast
import json
import uuid
import fnmatch
import pickle
from typing import List, Dict


# TODO : handle wild-card imports


class Module:

    def __init__(self,file_path : str):
        self.file_path = file_path
        self.name : str = os.path.basename(file_path)
        self.childrens : List = []


class Code:

    def __init__(self, file_path: str, code_text : str = ""):

        self.file_path = file_path
        self.name : str = os.path.basename(file_path)
        self.text : str = code_text
        self.local_imports = set() 
        self.external_imports = set() 
        self.called_entities = set()




class DirecTree:

    def __init__(self , path : str,\
                 file_extensions : List[str] = ["py"],\
                 ignores : List[str] = []) -> None:

        self.tree = None
        self.root_path = os.path.abspath(path)
        self.tree_struct = None
        self.file_extensions = file_extensions

        self.node_map = {} 
        self.file_is_visited = set()


        self.head : Module = Module(self.root_path)
        self.is_already_initialized : bool = False
        self.ignores : List = list(filter(lambda x: True if (not x.startswith('#') and x!="") else False,ignores))  if ignores else None
        self.storage_path :str = os.path.join(self.root_path,'.storage')
        self.meta_data_loc : str = os.path.join(self.storage_path,'.meta_data.json')

        self.encode_path = lambda path : re.sub("[^\w]","_",path)
        self.get_called_entities = lambda x: x.split(' ')[-1].split(',')
        
        # if os.path.exists(self.storage_path):
        #     self.is_already_initialized = True

        os.makedirs(self.storage_path,exist_ok=True)
        
        if self.is_already_initialized:
            self.meta_data : Dict = json.load(open(self.meta_data_loc,'r'))
        else:
            self.meta_data : Dict = {}
            self.tree = self.__create_tree__(self.head)
            self.tree_struct = self.__connect_imports__(self.tree,0,self.tree.name)
            # print(self.nodes)

            json.dump(self.meta_data,open(self.meta_data_loc,'w'))


    def __create_file__(self, path : str):

        file_id = str(uuid.uuid4())

        file_data = {"id":file_id, "full_text":"".join(open(path,'r').readlines())}

        file_new_path = os.path.join(self.storage_path,'.'+file_id+".json")
        
        json.dump(file_data,open(file_new_path,'w'),indent=3) 

        self.meta_data[self.encode_path(path)]= {"file_path": path , "data_path" : file_new_path}

    def __create_tree__(self, node: Module) -> Module:

        for child in sorted(os.listdir(node.file_path)):
            
            if not ( child.startswith(".") or any(fnmatch.fnmatch(child, pattern.strip("/")) for pattern in self.ignores)):

                child_path = os.path.join(node.file_path,child)
                
                if os.path.isdir(child_path) :

                    node.childrens.append(self.__create_tree__(Module(child_path)))
                                
                elif any([True if child.endswith(e) else False for e in self.file_extensions]):
                    
                    code_node = Code(file_path=child_path)
                    node.childrens.append(code_node)
                    self.node_map[child_path] = code_node

        return node

    def __connect_imports__(self,head : Module, level : int, path_name : str ) -> str:

        tree_struct = path_name

        for child in head.childrens:

            if isinstance(child,Module):

                path_name = f'\n{"  "*(level+1)}|{"--"*(level+1)} {child.name}'
                tree_struct  += path_name
                tree_struct  += self.__connect_imports__(child,level+1,"\t")

            else:
                path_name = f'\n{"  "*(level+1)}|{"--"*(level+1)} {child.name}'
                tree_struct  += path_name
                
                # self.__create_file__(child)
                self.__find_imports_(child)

        return tree_struct
    
    def __import_to_path__(self,base_file_path: str, module_name: str,level: int = 0):

            if level > 0:
                base_dir = os.path.dirname(base_file_path)
                
                target_dir = base_dir
                for _ in range(level - 1):
                    target_dir = os.path.dirname(target_dir)

                target_path_base = os.path.join(target_dir, module_name.replace('.', os.sep)) if module_name else target_dir
                
                potential_file = target_path_base + '.py'
                if os.path.exists(potential_file):
                    return potential_file
                    
                potential_init = os.path.join(target_path_base, '__init__.py')
                if os.path.exists(potential_init):
                    return potential_init

                return None

            relative_path = module_name.replace('.', os.sep)
            
            potential_file = os.path.join(self.root_path, relative_path + '.py')
            if os.path.exists(potential_file):
                return potential_file
                
            potential_init = os.path.join(self.root_path, relative_path, '__init__.py')
            if os.path.exists(potential_init):
                return potential_init

            return None

    def __find_imports_(self, child : Code):

        if child.file_path in self.file_is_visited or not child.file_path.endswith('.py'):
            return 
        
        if not child.file_path.startswith(os.path.abspath(self.root_path)):
            return
        
        self.file_is_visited.add(child.file_path)

        try:
            code_text = open(child.file_path,'r').read()
            code_tree = ast.parse(code_text)
            child.text = code_text

        except Exception as e:
            print(f'{e} occured during parsing code')
            return
    
        nodes_to_recurse = set()

        for node in ast.walk(code_tree):
            
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                
                if isinstance(node, ast.Import):
                    module_name = node.names[0].name 
                    level = 0
                else: 
                    module_name = node.module
                    level = node.level 

                if not module_name and level == 0:
                    continue

                resolved_path = self.__import_to_path__(child.file_path, module_name, level)
                
                if resolved_path:

                    child.local_imports.add(resolved_path)

                    if resolved_path in self.node_map:

                        resolved_node = self.node_map[resolved_path]

                    else:
                        resolved_node = Code(resolved_path)
                        self.node_map[resolved_path] = resolved_node
                        
                    try:
                        imported_code_text = open(resolved_path, 'r').read()
                        imported_code_tree = ast.parse(imported_code_text)
                    except Exception as e:
                        print(f'Failed to parse imported code at {resolved_path}: {e}')
                        continue 

                    
                    child.text += f"\n\n# --- Inlined Code from: {resolved_path} ---\n\n"

                    entities_to_find = node.names
                    
                    for alias in entities_to_find:
                        target_entity_name = alias.name
                        
                        for imported_node in ast.walk(imported_code_tree):
                            
                            is_definition = isinstance(imported_node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                            
                            if is_definition and imported_node.name == target_entity_name:
                                
                                try:
                                    entity_source = ast.get_source_segment(imported_code_text, imported_node)
                                    if entity_source:
                                        child.text += f"\n\n# Inlining {target_entity_name}\n"
                                        child.text += entity_source
                                        child.text += "\n"
                                        
                                        child.local_imports.add(resolved_path)
                                        entity_name_to_track = alias.asname if alias.asname else alias.name
                                        child.called_entities.add(entity_name_to_track)
                                        break 
                                
                                except Exception as e:
                                    print(f"Error getting source segment for {target_entity_name} in {resolved_path}: {e}")
                                    
                    nodes_to_recurse.add(resolved_node)

                else:
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            child.external_imports.add(alias.name.split('.')[0])
                    elif node.module:
                        child.external_imports.add(node.module.split('.')[0])

        for resolved_node in nodes_to_recurse:
            self.__find_imports_(resolved_node)

        
        
        print(child,child.file_path,child.called_entities,child.local_imports,child.text)

        
            