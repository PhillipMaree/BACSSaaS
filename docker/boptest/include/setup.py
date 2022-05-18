import os, shutil, sys

if __name__ == '__main__':
    
    src_path = os.path.join(sys.argv[1], 'project1-boptest') 
    dst_path = os.path.join(os.getcwd(),'')
    
    print('Current wokring directory is: {}'.format(src_path))
    print('Final source directory is: {}'.format(dst_path))
    
    # extract and prepare necessary folder structure

    for testcase in os.listdir(os.path.join(src_path,'testcases')):
        if os.path.isdir(os.path.join(src_path, 'testcases', testcase)):

            src = os.path.join(src_path, 'testcases', testcase, 'models')
            dst = os.path.join(dst_path, 'models', testcase)
            os.makedirs(dst)
          
            print('Transfer models: <{}> -> <{}>'.format(src, dst))
            
            for file in os.listdir(src):
                if file.endswith('.fmu'):
                    shutil.copy(os.path.join(src,file), os.path.join(dst,file))
                
            src = os.path.join(src_path, 'testcases', testcase, 'doc')
            dst = os.path.join( dst_path, 'doc', testcase)
            
            print('Transfer doc: <{}> -> <{}>'.format(src, dst))
                        
            shutil.copytree(src, dst)
                
    # copy remainder of files
  
    shutil.copy(os.path.join(src_path, 'restapi.py'), os.path.join(dst_path,'restapi.py'))        # NOTE JP.Maree have modified verion in include version to switch between testcases
    shutil.copy(os.path.join(src_path, 'testcase.py'), os.path.join(dst_path,'testcase.py'))
    shutil.copy(os.path.join(src_path, 'version.txt'), os.path.join(dst_path,'version.txt'))

    shutil.copytree(os.path.join(src_path, 'data'), os.path.join(dst_path, 'data'))
    shutil.copytree(os.path.join(src_path, 'forecast'), os.path.join(dst_path, 'forecast'))
    shutil.copytree(os.path.join(src_path, 'kpis'), os.path.join(dst_path, 'kpis'))
