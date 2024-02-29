import argparse
import yaml
from bs4 import BeautifulSoup
import random
import os, sys, re
import requests
from bs4 import BeautifulSoup
import time
import datetime
import warnings

from selenium import webdriver 
from selenium.webdriver import Firefox 
from selenium.webdriver.common.by import By 

import threading

counter = 0
timestamp = 0

param_dict = {  'name': '',
                'sitemaps' : './sitemaps/name_sitemap.xml',
                'template' : None,
                'run_analysis' : True,
                'rpm' : 150,
                'sample_size' : 5,
                'limit' : 5,
                'folderExists' : False,
                'show_sleep' : False,
                'shuffle' : True,
                'overwrite' : False,
                'javascript_generated':False,
                'javascript_wait_time': 3,
                'threads_num': 1,
                }

warning_flag = True

def parse_args():
    parser = argparse.ArgumentParser(description='Download html files from sitemap.xml')
    parser.add_argument('--cfg', dest='cfg_file',
                        help='config file',
                        default='cfg/birds_proGAN.yml', type=str)
    
    args = parser.parse_args()
    return args

def checkParams(params):
    if not isinstance(params['name'], str):
        raise Exception('name must be a string')
    
    if len(params['name']) == 0:
        raise Exception('name must must not be empty')
    
    if not isinstance(params['sitemaps'], str) and  not isinstance(params['sitemaps'], list):
        raise Exception('sitemaps must be a string or a list of strings')
    
    if isinstance(params['sitemaps'], list) and  any(not isinstance(l, str) for l in params['sitemaps']):
        raise Exception('all sitemaps must be a string')
    
    if len(params['sitemaps'])  == 0:
        raise Exception('sitemaps must not be empty')
    
    if not isinstance(params['run_analysis'], bool):
        raise Exception('run_analysis must be bool')
    
    if not isinstance(params['sample_size'], int):
        raise Exception('sample_size must be int')
    
    if params['sample_size'] < 1:
        raise Exception('sample_size cannot be less than one')
    
    if not isinstance(params['rpm'], int):
        raise Exception('rpm must be int')
    
    if params['rpm'] < 1:
        raise Exception('rpm cannot be less than one')
    
    if params['limit'] != None and not isinstance(params['limit'], int):
        raise Exception('limit must be either None (null in yml file) or int')
    
    if params['limit'] != None and params['limit'] < 1:
        raise Exception('limit cannot be less than one')
    
    if not isinstance(params['folderExists'], bool):
        raise Exception('folderExists must be bool')
    
    if not isinstance(params['show_sleep'], bool):
        raise Exception('show_sleep must be bool')
    
    if not isinstance(params['shuffle'], bool):
        raise Exception('shuffle must be bool')
    
    if not isinstance(params['overwrite'], bool):
        raise Exception('overwrite must be bool')

    if params['template'] != None and not isinstance(params['template'], str):
        raise Exception('limit must be either None (null in yml file) or string')
    
    if params['template'] != None and len(params['template']) == 0:
        raise Exception('template str cannot be empty')
    
    if not isinstance(params['javascript_generated'], bool):
        raise Exception('javascript_generated must be bool')
    
    if params['javascript_wait_time'] != None and not isinstance(params['javascript_wait_time'], int):
        raise Exception('javascript_wait_time must be either None (null in yml file) or int')
    
    if params['javascript_wait_time'] != None and params['javascript_wait_time'] < 0:
        raise Exception('javascript_wait_time cannot be negative')
    
    
def readSiteMap(sitemaps, template):
    answer = []
    sitemap_list = []
    if isinstance(sitemaps, str):
        sitemap_list = [sitemaps]
    else:
        sitemap_list = sitemaps

    for sitemap in sitemap_list:

        with open(sitemap, 'r', encoding="utf8") as f:
            data = f.read()

        soup = BeautifulSoup(data, 'html.parser')

        global warning_flag
        if warning_flag:
            print()
            print('Ignore this warning, html-like treatment is desired, otherwise unrelated links will also be included.')
            print()
            warning_flag = False

        locTags = soup.find_all("loc")

        for tag in locTags:

            if template:
                if re.match(template, tag.text):
                    answer.append(tag.text)
            else:
                answer.append(tag.text)

    return answer

def linkLoader(list, name, shuffle, overwrite):
    copy = list.copy()
    if shuffle:
        random.shuffle(copy)
    if overwrite:
        for c in copy:
            yield c
    else:
        for c in copy:
            filename = re.sub('\W+', '-', c) +'.html'
            path = os.path.join('output', name, filename)
            if not os.path.exists(path):
                yield c

# credit: https://stackoverflow.com/a/62207356
def savePage(url, folder):
    
    session = requests.Session()
    #... whatever other requests config you need here
    response = session.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    filename = re.sub('\W+', '-', url) +'.html'
    path = os.path.join('output', folder, filename)
    
    if not os.path.exists(path):
        with open(path, 'wb') as file: # saves modified html doc
            file.write(soup.prettify('utf-8'))
        return True
    return False

def savePageJavaScript(url, folder, driver, wait_time):    

    driver.get(url) 

    time.sleep(wait_time)

    
    while url.strip() != driver.current_url:
        time.sleep(1)


    html_text = driver.find_element(By.TAG_NAME,'html').get_attribute('innerHTML')
    if html_text:
        soup = BeautifulSoup(html_text, "html.parser")
        filename = re.sub('\W+', '-', url) +'.html'
        path = os.path.join('output', folder, filename)
        if not os.path.exists(path):
            with open(path, 'wb') as file: # saves modified html doc
                file.write(soup.prettify('utf-8'))
            return True
    return False

def getDriver():
    options = webdriver.FirefoxOptions() 
    options.add_argument("--headless") 
    options.page_load_strategy = "none"
    driver = Firefox(options=options) 
    driver.implicitly_wait(5)
    return driver

def threadTask(time_lock, lock, generator, total_count, perfect_dt, javascript_generated):
    global counter
    global timestamp
    thread_counter = 0
    local_counter = 0

    
    if javascript_generated:
        driver = getDriver()

    while True:

        with lock:
            try:
                link = next(generator)
            except StopIteration:    
                driver.quit()
                return
            
            local_counter = counter

            counter = counter + 1

        if limit != None and local_counter >= limit:
            break

        download_success = False

        if driver:
            download_success = savePageJavaScript(link, name, driver, javascript_wait_time)
            
            if thread_counter > 0 and thread_counter % 20000 == 0:
                print('Reloading webdriver')
                driver.quit()
                driver = getDriver()
                print('Webdriver reloaded\n')

        else:
            download_success = savePage(link, name)

        dt = time.time() - timestamp
        
        thread_counter = thread_counter + 1

        sleeptime = 0

        if dt < perfect_dt:
            sleeptime = perfect_dt - dt

        # sleeptime = perfect_dt + (random.random() * 2 - 1) * 0.25 * perfect_dt

        if show_sleep:
            print('sleep for', sleeptime)
            print()

        time.sleep(sleeptime)

        dt = time.time() - timestamp
        current_rpm = 60 / dt if dt > 0 else 0

        estimated_time = dt * (total_count - local_counter)
        hours = int(estimated_time / 3600)
        minutes = int((estimated_time - hours * 3600) / 60)
        seconds = int((estimated_time - hours * 3600 - minutes*60))


        print('Progress: {:5d} / {:5d}; dt {:.2f}; current rpm {:.2f}; ETA: {:s}\n{:s}: {:s}                                               '
            .format(local_counter, 
                    total_count, 
                    dt, 
                    current_rpm, 
                    '{:02d}:{:02d}:{:02d}'.format(hours, minutes, seconds),
                    'Downloaded' if download_success else 'Failed',
                    link))
        
        print()
        
        with time_lock:
            timestamp = time.time()

if __name__ == '__main__':
    args = parse_args()
    params = []

    if args.cfg_file is not None:
        with open(args.cfg_file) as stream:
            params = yaml.safe_load(stream)
    else:
        raise Exception('Config file not provided')
    
    if not os.path.isdir('./output'):
        os.mkdir('./output')

    for k in params.keys():
        if k not in param_dict.keys():
            if k == 'sitemap':
                raise Exception('\'sitemap\' parameter was replaced with \'sitemaps\', that accepts both string and list of string '.format(k))
            raise Exception('Unknown keys in param file {:s}'.format(k))
        
    for (k,v) in params.items():
        param_dict[k] = v

    checkParams(param_dict)

    print('Params:\n {:s}\n\n'.format(str(param_dict)))

    name = param_dict['name']
    sitemaps = param_dict['sitemaps']
    run_analysis = param_dict['run_analysis']
    rpm = param_dict['rpm']
    sample_size = param_dict['sample_size']
    limit = param_dict['limit']
    folderExists = param_dict['folderExists']
    show_sleep = param_dict['show_sleep']
    shuffle = param_dict['shuffle']
    overwrite = param_dict['overwrite']
    template = param_dict['template']
    javascript_generated = param_dict['javascript_generated']
    javascript_wait_time = param_dict['javascript_wait_time']
    threads_num = param_dict['threads_num']


    links = readSiteMap(sitemaps, template)

    if run_analysis:
        print('Total files count: {:d}'.format(len(links)))
        print('First {:d} records'.format(sample_size))

        for i in range(min(sample_size, len(links))):
            print(links[i])

        print('')
        print('{:d} random records'.format(sample_size))
        
        for i in random.sample(links, min(sample_size, len(links))):
            print(i)
        
        sys.exit()

    try:
        os.mkdir(os.path.join('output', name))
    except Exception as e:
        if isinstance(e, FileExistsError):
            if folderExists:
                warnings.warn('Destination folder already exists')
                print()
                time.sleep(1.5)
            else:
                raise e

    counter = 0
    total_count = len(list(linkLoader(links, name, shuffle, overwrite))) if limit == None else limit
    perfect_dt = 60 / rpm
    timestamp = time.time()
    # print(perfect_dt)
    dt = 0
    driver = None

    generator = linkLoader(links, name, shuffle, overwrite)

    lock = threading.Lock()
    time_lock = threading.Lock()

    threads = []

    for i in range(threads_num):
        threads.append(threading.Thread(target=threadTask, args=(time_lock, lock, generator, total_count, perfect_dt, javascript_generated,)))

    for th in threads:
        th.start()

    for th in threads:
        th.join()

    print('Done')


    
    
    

    