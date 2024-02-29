import argparse
import os
import pickle
import shutil

import pandas as pd

counter = 0

failed_count = 0

def parse_args():
    parser = argparse.ArgumentParser(description='Convert folder with html files to folder with text files and metadata dict in pickle')
    parser.add_argument('--cls', dest='cls_name',
                        help='Extractor class name',
                        default='', type=str)
    
    parser.add_argument('--in', dest='in_fold',
                        help='folder with html in \\input',
                        default='', type=str)
    
    parser.add_argument('--out', dest='out_fold',
                        help='folder with results \\output',
                        default='', type=str)
    
    parser.add_argument('--ovw', dest='overwrite',
                        help='flag for deleting the output folder if it already exists',
                        default=False, type=bool)
    
    parser.add_argument('--cnt', dest='cont',
                        help='flag for continuing the started extraction',
                        default=False, type=bool)
    
    parser.add_argument('--cio', dest='cio',
                        help='optional, acts alias for --cls, --in and --out combined',
                        default='', type=str)
    
    parser.add_argument('--thr', dest='thr',
                        help='number of threads',
                        default=1, type=int)
    
    parser.add_argument('--chk', dest='chk',
                        help='Rate of saving metadata',
                        default=1000, type=int)
    
    args = parser.parse_args()
    return args

def checkArgss(args):
    if not isinstance(args.cio, str):
        raise Exception('cio must be a string')
    
    if not args.chk > 0:
        raise Exception('chk must be more than 0')
    
    if len(args.cls_name.split('.')) > 1:
        raise Exception('provide cls_name without extention')
    
    if len(args.cio) > 0:
        return

    if len(args.cls_name) == 0:
        raise Exception('cls_name must must not be empty')
    

    if len(args.in_fold) == 0:
        raise Exception('in_fold must must not be empty')

    if len(args.out_fold) == 0:
        raise Exception('out_fold must must not be empty')
    
def threadTask(lock_meta, lock_iter, lock, generator, extractorCls, total_count, metadata_dict):
    global counter
    global failed_count
    local_counter = 0
    extractor = extractorCls()
    while True:
        with lock_iter:
            try:
                file = next(generator)
            except StopIteration:    
                return
            local_counter = counter
            counter = counter + 1


        with open(os.path.join(input_folder, file), encoding='utf-8') as f:
            html_txt = f.read()
        try:
            (text, metadata) = extractor.extract(html_txt)
            file_name =  os.path.splitext(file)[0]

            with lock_meta:
                metadata_dict[file_name] = metadata

            with open(os.path.join(output_folder, 'text', file_name + '.txt'), encoding='utf-8', mode='w') as f:
                f.writelines(text)
            print('{:3d}/{:3d} ({:3.2f}%): \tParsed: {:s}'.format(local_counter, total_count, (float(local_counter) / total_count) * 100, file))
        except Exception as e:
            err_str = '{:3d}/{:3d} ({:3.2f}%): \tFailed to parse: {:s} :\n {:s}'.format(local_counter, total_count, (float(local_counter) / total_count) * 100, file, str(e))
            print(err_str)
            with lock:
                failed_count = failed_count + 1
                with open('failedlinks.txt', mode='a') as f:
                        f.write(err_str + '\n\n')
                pass

def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

def links_generator(links, passed_links):
    for link in links:
        if not os.path.splitext(link)[0] in passed_links:
            yield link

def save_metadata(output_folder, metadata_dict):
    metadata_path = os.path.join(output_folder, 'metadata.pickle')
    metadata_path_prev = os.path.join(output_folder, 'metadata_prev.pickle')

    if os.path.exists(metadata_path):
        if os.path.exists(metadata_path_prev):
            os.remove(metadata_path_prev)
        os.rename(metadata_path, metadata_path_prev)
    
    with open(metadata_path, 'wb') as handle:
        pickle.dump(metadata_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

if __name__ == '__main__':
    args = parse_args()

    checkArgss(args)

    if len(args.cio) > 0:
        if len(args.in_fold) == 0:
            args.in_fold = args.cio

        if len(args.out_fold) == 0:
            args.out_fold = args.cio

        if len(args.cls_name) == 0:
            args.cls_name = args.cio

    HTMLextractor = None
    if args.cls_name is not None:
        HTMLextractor = __import__('extr.' + args.cls_name, globals(), locals(), ['HTMLextractor']).HTMLextractor
    else:
        raise Exception('Class file not provided')
    
    if not os.path.isdir('./output'):
        os.mkdir('./output')

    input_folder = os.path.join('input', args.in_fold)
    output_folder = os.path.join('output', args.out_fold)

    
    if os.path.exists(output_folder) and  args.overwrite:
        shutil.rmtree(output_folder)

    if not args.cont:
        try:
            os.mkdir(output_folder)
            os.mkdir(os.path.join(output_folder, 'text'))
        except Exception as e:
            raise e
    
    with open('failedlinks.txt', mode='w') as f:
        f.write('')
    
    metadata_dict = {}

    if args.cont:
        metadata_dict = pd.read_pickle(os.path.join(output_folder, 'metadata.pickle'))

    total_count = 0
    failed_count = 0

    failed_log = ''
    for root, dirs, files  in os.walk(input_folder, topdown=False):
        counter = 0
        total_count = len(files)

        if args.cont:
            total_count = total_count - len(metadata_dict.keys())
        extractor = HTMLextractor()

        print(metadata_dict.keys())

        for file in links_generator(files, metadata_dict.keys()):
            counter = counter + 1
            with open(os.path.join(input_folder, file), encoding='utf-8') as f:
                html_txt = f.read()
            try:
                (text, metadata) = extractor.extract(html_txt)
                file_name =  os.path.splitext(file)[0]

                metadata_dict[file_name] = metadata

                with open(os.path.join(output_folder, 'text', file_name + '.txt'), encoding='utf-8', mode='w') as f:
                    f.writelines(text)
                    
                print('{:3d}/{:3d} ({:3.2f}%): \tParsed: {:s}'.format(counter, total_count, (float(counter) / total_count) * 100, file))
            except Exception as e:
                err_str = '{:3d}/{:3d} ({:3.2f}%): \tFailed to parse: {:s} :\n {:s}'.format(counter, total_count, (float(counter) / total_count) * 100, file, str(e))
                print(err_str)
                failed_count = failed_count + 1
                with open('failedlinks.txt', mode='a') as f:
                        f.write(err_str + '\n\n')
                pass

            if args.chk > 0 and counter % args.chk == 0:
                save_metadata(output_folder, metadata_dict)
    

    save_metadata(output_folder, metadata_dict)
        
    print('Done, failed {:d} out of {:d} ({:2.2f}%)'.format(failed_count, total_count, float(failed_count) / total_count))
    




    
    
    

    