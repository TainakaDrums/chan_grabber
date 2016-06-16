from __future__ import print_function
import lxml.html as html
import sys
import threading
import os.path
import os
import argparse
import time
from itertools import chain
from etaprogress.progress import ProgressBar

if sys.version_info.major == 2:
    from urlparse import urlparse
    from urllib import quote
    import urllib2
    from urllib2 import HTTPError
    import Queue as queue
else:
    from urllib.parse import urlparse
    from urllib.parse import quote
    import urllib.request as urllib2
    from urllib.error  import HTTPError as HTTPError
    import queue



class Download_pics(threading.Thread):

    def __init__ (self):
        threading.Thread.__init__(self)
        self.daemon = True

    def run(self):

        while True:
            page=None
            link=q.get()
            file_name=link.split("/")[-1]

            pic_url=urllib2.Request(url_treatment(link),
                headers=headers)

            while not page:
                try:
                    page=urllib2.urlopen(pic_url)
                except HTTPError as e:
                    if e.getcode() == 503:
                        time.sleep(2)
                    else:
                        print(e.getcode(), e.url)
                        break


            if page and page.getcode() == 200 :
                data=page.read()

                if data:
                    with open( os.path.join(path, file_name) , "wb") as file:
                        file.write(data)

            bar.numerator += 1
            print(bar, end='\r')
            sys.stdout.flush()
            q.task_done()


def create_dir_name(parsed_link):
    thread=parsed_link.path.split("/")[-1].split(".")[0]
    section=parsed_link.path.split("/")[1]
    host=parsed_link.hostname.split(".")[-2]

    dir_name="_".join( (host, section, thread) )

    if os.path.split(os.getcwd())[-1] == dir_name:
        dir_name=os.getcwd()

    return dir_name


def url_treatment(pic_url):

    pic_url=quote(pic_url, ":/")

    if pic_url.startswith("//"):
        pic_url=parsed_link.scheme+":"+pic_url
    elif pic_url.startswith("../"):
        fragments = parsed_link.geturl().split("/")[:-2]
        fragments.append(pic_url.lstrip("../"))
        pic_url="/".join(fragments)
    elif not pic_url.startswith("http"):
        pic_url=parsed_link.scheme+"://"+parsed_link.hostname+pic_url

    return pic_url


types={"all": (".jpeg", ".jpg", ".png", ".bmp", ".gif", ".webm"),
       "pic": (".jpeg", ".jpg", ".png", ".bmp"),
       "gif":  (".gif", ),
       "webm": (".webm",)
       }


parser = argparse.ArgumentParser(description="Download content from imageboard thread")

parser.add_argument(
    "-l",
    "-u",
    "--url",
    "--link",
    action='store',
    dest='thread_link',
    type=str,
    required=True,
    help='Link to thread'
)

parser.add_argument(
    "-t",
    "--type",
    action='store',
    dest='types',
    type=str,
    choices=types.keys(),
    nargs="*",
    default= ("all",),
    required=False,
    help='Type of content'
)

parser.add_argument(
    "-o",
    action='store',
    dest='path',
    type=str,
    required=False,
    help='Path'
)


if __name__ == '__main__':

    args = parser.parse_args()


    headers={"User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:21.0) Gecko/20100101 Firefox/21.0"}
    link=urllib2.Request(args.thread_link, headers=headers)
    parsed_link=urlparse(args.thread_link.strip().rstrip("/"))
    preferred_types= tuple( chain.from_iterable( (types[type]  for type in args.types) ) )


    if args.path:
        path=args.path
    else:
        path=create_dir_name(parsed_link)

    if not os.path.isdir(path):
        os.makedirs(path)

    try:
        page=urllib2.urlopen(link)
    except HTTPError as e:
        print("Can't open url. Code %d" % e.getcode() )
        exit()


    doc=html.document_fromstring(str(page.read()))
    res=doc.findall(".//a[@target='_blank']")
    links={i.attrib['href'].split(":")[-1]    for i in res  if  i.attrib['href'].endswith(preferred_types) }

    q=queue.Queue()

    for link in links:
        if  not os.path.exists( os.path.join( path, link.split("/")[-1])  ):
            q.put(link)

    bar = ProgressBar(q.qsize(), max_width=60)
    bar.numerator = 0

    for _ in range(10):
        thread=Download_pics()
        thread.start()

    q.join()
    print()
