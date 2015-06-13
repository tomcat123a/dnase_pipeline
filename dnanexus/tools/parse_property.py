#!/usr/bin/env python2.7
# parse_property.py  Reads property string and prses a requested value.
#                    Write request to stdout and verbose info to stderr.  This allows easy use in dx app scripts.

# imports needed for Settings class:
import os, sys, string, argparse, json
import dxpy

def env_get_current_project_id():
    ''' Returns the current project name for the command-line environment '''
    err, proj_name = commands.getstatusoutput('cat ~/.dnanexus_config/DX_PROJECT_CONTEXT_NAME')
    if err != 0:
        return None
    proj = dxencode.get_project(proj_name)
    return proj.get_id()
    
    return proj_name

def get_dxfile(filePath,project=None):
    '''Returns dxfile object.'''
    dxfile = None
    #if filePath.find("$dnanexus_link") != -1:
    #    filePath = filePath.split(' ')[1]
    #    filePath = filePath.replace("'","").replace('"','').replace("}","").replace("{","")
    try:
        dxlink = json.loads(filePath.strip("'"))
    except:
        dxlink = None
        
    if project != None:
        
        try:
            if dxlink != None:
                dxfile = dxpy.get_handler(dxlink,project=project)
            else:
                dxfile = dxpy.get_handler(filePath,project=project)
        except:
            try:
                dxlink = dxpy.dxlink(filePath,project=project)
                dxfile = dxpy.get_handler(dxlink)
            except:
                try:
                    proj_id = env_get_current_project_id()
                    dxfile = dxpy.DXFile(filePath,project=proj_id)
                except:
                    sys.stderr.write('ERROR: unable to find file "' + filePath + '": \n')
                    sys.exit(0)  # Do not error on tool run in dx script 
    
    else:
    
        try:
            if dxlink != None:
                dxfile = dxpy.get_handler(dxlink)
            else:
                dxfile = dxpy.get_handler(filePath)
        except:
            try:
                dxlink = dxpy.dxlink(filePath)
                dxfile = dxpy.get_handler(dxlink)
            except:
                try:
                    proj_id = env_get_current_project_id()
                    dxfile = dxpy.DXFile(filePath,project=proj_id)
                except:
                    sys.stderr.write('ERROR: unable to find file "' + filePath + '": \n')
                    sys.exit(0)  # Do not error on tool run in dx script 

    if dxfile == None:
        sys.stderr.write('ERROR: unable to find file "' + filePath + '": \n')
        sys.exit(0)  # Do not error on tool run in dx script 
    
    return dxfile


def file_get_property(filePath,key,subkey,return_json=False,project=None,verbose=False):
    '''Returns dx file's property matching 'key'.'''

    dxfile = get_dxfile(filePath,project=project)
    
    props = dxfile.get_properties()
    if not props:
        sys.stderr.write('ERROR: unable to find properties for file "' + filePath + '": \n') 
        sys.exit(0)  # Do not error on tool run in dx script 
    
    if key not in props:
        sys.stderr.write('ERROR: unable to find "'+key+'" in properties for file "' + filePath + '": \n') 
        sys.exit(0)  # Do not error on tool run in dx script
    props = props[key]
         
    if return_json or subkey != None:
        try:
            props = json.loads(props)
        except:
            try:
                props = json.loads("{"+props+"}")
            except:
                sys.stderr.write('Failure parsing "'+props+'" as json.\n') 
                sys.exit(0)  # Do not error on tool run in dx script

    if subkey != None:
        if subkey not in props:
            sys.stderr.write('ERROR: unable to find "'+subkey+'" in properties for file "' + filePath + '": \n') 
            sys.exit(0)  # Do not error on tool run in dx script
        props = props[subkey]
        
    if verbose:
        sys.stderr.write(props + '\n')
    
    return props

def file_describe(filePath,key=None,project=None,verbose=False):
    '''Returns dx file's description property matching 'key'.'''

    dxfile = get_dxfile(filePath,project=project)    
    
    desciption = dxfile.describe()
    if not desciption:
        sys.stderr.write('ERROR: unable to find description of file "' + filePath + '": \n') 
        sys.exit(0)  # Do not error on tool run in dx script 
    
    if key == None:
        if verbose:
            sys.stderr.write(json.dumps(desciption) + '\n')
        return desciption
    
    if key not in desciption:
        sys.stderr.write('ERROR: unable to find "'+key+'" in description of file "' + filePath + '": \n') 
        sys.exit(0)  # Do not error on tool run in dx script
    value = desciption[key]
         
    if verbose:
        sys.stderr.write(value + '\n')
    
    return value

def file_create_root(filePath,project=None,verbose=False):
    '''Returns a standard file name root when in folder {exp_acc}/repN_N.'''

    folder = file_describe(filePath,'folder',project=project,verbose=False)
    folders = folder.split('/')
    exp = ''
    rep = folders[-1]
    if not rep.startswith('rep'):
        exp = rep
        rep = ''
    if len(folders) > 1 and exp == '':
        exp = folders[-2]
    if exp != '' and not exp.startswith('ENCSR'):
        exp = ''
    root = exp
    if root != '' and rep != '':
        root += '_' + rep
         
    if verbose:
        sys.stderr.write(root + '\n')
    if root == '':
        sys.stderr.write("Found nothing for root: folder["+folder+"] path ["+filePath+"] \n")
        desc = file_describe(filePath,project=project,verbose=False)
        sys.stderr.write(json.dumps(desc,indent=4) + '\n')
    
    return root

def file_find_rep(filePath,project=None,verbose=False):
    '''Returns the replicate tag when in folder {exp_acc}/repN_N.'''

    folder = file_describe(filePath,'folder',project=project,verbose=False)
    folders = folder.split('/')
    rep = folders[-1]
    if not rep.startswith('rep'):
        rep = ''
        # Very limited success with file names
        name = file_describe(filePath,'name',verbose=False)
        for part in name.split('/'):
            if part.startswith('rep'):
                rep = part
            elif rep != '':
                if part in ['1','2','3','4','5','6','7','8','9']:
                    rep += '_' + part
                else:
                    break
         
    if verbose:
        sys.stderr.write(rep + '\n')
    if rep == '':
        sys.stderr.write("Found nothing for rep: folder["+folder+"] path ["+filePath+"] \n")
        desc = file_describe(filePath,project=project,verbose=False)
        sys.stderr.write(json.dumps(desc,indent=4) + '\n')
    
    return rep

def file_find_exp_id(filePath,project=None,verbose=False):
    '''Returns the experiment id (accession) when in folder {exp_acc}/repN_N.'''

    folder = file_describe(filePath,'folder',verbose=False)
    exp = ''
    for part in folder.split('/'):
        if part.startswith('ENCSR'):
            exp = part
            break
    
    if verbose:
        sys.stderr.write(exp + '\n')
    
    return exp

def main():
    parser = argparse.ArgumentParser(description =  "Creates a json string of qc_metrics for a given applet. " + \
                                                    "Returns string to stdout and formatted json to stderr.")
    parser.add_argument('-f', '--file',
                        help='DX id, link or path to file.',
                        required=True)
    parser.add_argument('-p','--property',
                        help="Property name.",
                        default='QC',
                        required=False)
    parser.add_argument('-s','--subproperty',
                        help="Property name.",
                        default=None,
                        required=False)
    parser.add_argument('-k', '--key',
                        help='Prints just the value for this key.',
                        default=None,
                        required=False)
    parser.add_argument('--keypair',
                        help='Prints the key: value pair for this key.',
                        default=None,
                        required=False)
    parser.add_argument('--project',
                        help="Project (especially helpfule when calling from DX app).",
                        default=None,
                        required=False)
    parser.add_argument('--root_name', action="store_true", required=False, default=False, 
                        help="Return a standardized file name root based on file location.")
    parser.add_argument('--rep_tag', action="store_true", required=False, default=False, 
                        help="Return a rep tag based on file location.")
    parser.add_argument('--exp_id', action="store_true", required=False, default=False, 
                        help="Return the exp_id based on file location.")
    parser.add_argument('-d', '--describe', action="store_true", required=False, default=False, 
                        help="Look for key in file description.")
    parser.add_argument('-j', '--json', action="store_true", required=False, default=False, 
                        help="Expect json.")
    parser.add_argument('-q', '--quiet', action="store_true", required=False, default=False, 
                        help="Suppress non-error stderr messages.")
    parser.add_argument('-v', '--verbose', action="store_true", required=False, default=False, 
                        help="Make some noise.")

    args = parser.parse_args(sys.argv[1:])
    if len(sys.argv) < 2:
        parser.print_usage()
        return
    
    if args.root_name:
        root = file_create_root(args.file,project=args.project,verbose=args.verbose)
        print root
        if not args.quiet:
            sys.stderr.write("root_name: '"+root+"'\n")
        sys.exit(0)
        
    elif args.exp_id:
        exp_id = file_find_exp_id(args.file,project=args.project,verbose=args.verbose)
        print exp_id
        if not args.quiet:
            sys.stderr.write("exp_id: '"+exp_id+"'\n")
        sys.exit(0)
        
    elif args.rep_tag:
        rep = file_find_rep(args.file,project=args.project,verbose=args.verbose)
        print rep
        if not args.quiet:
            sys.stderr.write("rep: '"+rep+"'\n")
        sys.exit(0)
        
    elif args.describe:
        value = file_describe(args.file,args.key,project=args.project,verbose=args.verbose)
        if args.key != None:
            print value
            if not args.quiet:
                sys.stderr.write(args.key + ": '"+value+"'\n")
            sys.exit(0)
        else:
            properties = value
    else:
        properties = file_get_property(args.file,args.property,args.subproperty,return_json=args.json, \
                                                                        project=args.project,verbose=args.verbose)
        
    # Print out the properties
    if args.key != None:
        if args.key in properties:
            print json.dumps(properties[args.key])
            if not args.quiet:
                sys.stderr.write(json.dumps(properties[args.key],indent=4) + '\n')
        else:
            print ''   
            if not args.quiet:
                sys.stderr.write('(not found)\n')
    elif args.keypair != None:
        if args.keypair in properties:
            print '"' + args.keypair + '": ' + json.dumps(properties[args.keypair])
            if not args.quiet:
                sys.stderr.write('"' + args.keypair + '": ' + json.dumps(properties[args.keypair],indent=4) + '\n')
        else:
            print '"' + args.keypair + '": '
            if not args.quiet:
                sys.stderr.write('"' + args.keypair + '": \n')
    else: 
        print json.dumps(properties)
        if not args.quiet:
            sys.stderr.write(json.dumps(properties,indent=4) + '\n')
    
if __name__ == '__main__':
    main()
