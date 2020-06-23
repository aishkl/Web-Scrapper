import scrapy
import os
import shutil
import json
import argparse
import datetime
import pandas as pd
from json import dumps
from argparse import ArgumentParser
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from fbcrawl.spiders.fbcrawl import FacebookSpider
from fbcrawl.spiders.comments import CommentsSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


parser = argparse.ArgumentParser()
parser.add_argument("-date", "--date", type=str , help="scrapper date",required=True)
parser.add_argument("-email", "--email", type=str , help="email",required=True)
parser.add_argument("-password", "--password", type=str , help="scrapper date",required=True)
parser.add_argument("-page", "--page", type=str , help="scrapper date",required=True)

args = parser.parse_args()
scrapper_date = args.date
email = args.email
password = args.password
page = args.page


@defer.inlineCallbacks
def crawl(runner):
    '''
    Runs the scrapper
    '''
    yield runner.crawl(FacebookSpider,email=email,password=password,page=page,date=scrapper_date,lang="en")
    yield runner.crawl(CommentsSpider,email=email,password=password,page=page,date=scrapper_date,lang="en")
    #yield runner.crawl(CommentsSpider,email="xyz@gmail.com",password="xyz",page="xyz",date="2019-12-23",lang="en")   
    reactor.stop()

def convert(s): 
    str1 = "" 
    return(str1.join(s)) 

def feed_output(path):
  post_list =[]
  input_fb = os.path.join(path, 'fb.json')
  output_fb = os.path.join(path, 'fb_posts.json')

  in_comments = os.path.join(path, 'comments.json')
  out_comments = os.path.join(path, 'fb_comments.json')
  

  #loading json data
  if os.path.isfile(input_fb):
    if os.stat(input_fb).st_size!=0:
      with open(input_fb,encoding='utf8') as f:
        data = json.load(f)

  #filter data as per the  scrapper date
      spilt_date = scrapper_date.split("-")
      sdate = datetime.date(int(spilt_date[0]),int(spilt_date[1]),int(spilt_date[2]))
      out_fb = [x for x in data if datetime.datetime.strptime(convert(x['date']), '%Y-%m-%d %H:%M:%S').date() >= sdate]

      with open(output_fb, 'w', encoding='utf8') as json_file:
        json.dump(out_fb, json_file, ensure_ascii=False)

  #fetching the post_ids for comments
      post_list = [i['post_id'] for i in out_fb]
    else:
        print("Facebook scrapper output is empty")
    os.remove(input_fb)
  else:
    print("Facebook posts scrapper was not used")

  #loading comments for posts
  if os.path.isfile(in_comments):
    if os.stat(in_comments).st_size!=0:
      with open(in_comments,encoding='utf-8') as f:
        data_comm = json.load(f)
        if post_list:
          output_comments =[x for x in data_comm if x['post_id'][0] in post_list]
        else:
          output_comments=data_comm

      with open(out_comments,'w',encoding='utf8') as json_file:
        json.dump(output_comments, json_file, ensure_ascii=False)
    else:
        print("Comments scrapper output is empty")
    os.remove(in_comments)
  else:
      print("Comments scrapper was not used")


def main():

  #Delete the results from the folder/files as you want to crawl different sites or the same site at different time-frames 
  # to avoid scrapy output  getting appended

  APP_ROOT = os.path.dirname(os.path.abspath(__file__))
  path = os.path.join(APP_ROOT,'output')

  filesToRemove = ['fb.json','comments.json']
  if os.path.exists(path):
    for i in filesToRemove:
        if os.path.exists(os.path.join(path, i)):
            os.remove(os.path.join(path, i))

  
  #Setting output format of the results saved
  settings = get_project_settings()
  settings.set("FEED_FORMAT", 'json')
  settings.set("FEED_URI", 'output/%(name)s.json' )

  configure_logging()
  runner = CrawlerRunner(settings)
  crawl(runner)
  reactor.run()
  feed_output(path)


if __name__ == "__main__":
  main()




