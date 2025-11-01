from src import direc_tree


dir_tree = direc_tree.DirecTree(path='demo',\
                                file_extensions=['.py','.cpy'],\
                                ignores = open('./.gitignore','r').read().split('\n'))
print(dir_tree.tree_struct)