import scrapy
import json

from scrapy.loader import ItemLoader
from scrapy.exceptions import CloseSpider
from fbcrawl.spiders.fbcrawl import FacebookSpider
from fbcrawl.items import CommentsItem, parse_date, parse_date2,FbcrawlItem,id_strip

from datetime import datetime
import datetime as d1
class CommentsSpider(FacebookSpider):
    """
    Parse FB comments
    """    
    name = "comments"
    custom_settings = {

        'FEED_EXPORT_FIELDS': ['post_id','source','reply_to','text','reactions', \
                              'url'],
        'DUPEFILTER_CLASS' : 'scrapy.dupefilters.BaseDupeFilter',
        'CONCURRENT_REQUESTS' : 1
    }

    def __init__(self, *args, **kwargs):
        if 'page' in kwargs:
            self.type = 'page'
        
        super().__init__(*args,**kwargs)

    def parse_page(self, response):
        '''
        '''

            #select all posts
        for post in response.xpath("//article[contains(@data-ft,'top_level_post_id')]"):
            many_features = post.xpath('./@data-ft').get()
            date = []
            date.append(many_features)
            date = parse_date(date,{'lang':self.lang})
            current_date = datetime.strptime(date,'%Y-%m-%d %H:%M:%S') if date is not None else date
    
            if current_date is None:
                date_string = post.xpath('.//abbr/text()').get()
                date = parse_date2([date_string],{'lang':self.lang})
                current_date = datetime(date.year,date.month,date.day) if date is not None else date                
                date = str(date)

            # prev_date = self.date -  d1.timedelta(days=1)
            # #print(prev_date > current_date)
            # if prev_date >= current_date:
            #     raise CloseSpider('Reached date: {}'.format(self.date))

            if abs(self.count) + 1 > self.max:
                raise CloseSpider('Reached max num of post: {}. Crawling finished'.format(abs(self.count)))
            self.logger.info('Parsing post n = {}, post_date = {}'.format(abs(self.count)+1,date))

            post_id = id_strip(post.xpath("./@data-ft").extract())

                #returns full post-link in a list
            post = post.xpath(".//a[contains(@href,'footer')]/@href").extract() 
            temp_post = response.urljoin(post[0])
            self.count -= 1
            yield scrapy.Request(temp_post, 
                                     self.parse_post, 
                                     priority = self.count,
                                     meta={'index':1,'post_id':post_id,'current_date':current_date})
    

            #load following page, try to click on "more"
            #if "more" link not present look for the highest year not parsed yet

        if self.group == 1:
            new_page = response.xpath("//div[contains(@id,'stories_container')]/div[2]/a/@href").extract()      
        else:
            new_page = response.xpath("//div[2]/a[contains(@href,'timestart=') and not(contains(text(),'ent')) and not(contains(text(),number()))]/@href").extract()      
 

        if not new_page: 
            self.logger.info('[!] "more" link not found, will look for a "year" link')
            #self.k is the year link that we look for 
            if response.meta['flag'] == self.k and self.k >= self.year:                
                xpath = "//div/a[contains(@href,'time') and contains(text(),'" + str(self.k) + "')]/@href"
                new_page = response.xpath(xpath).extract()
                if new_page:
                    new_page = response.urljoin(new_page[0])
                    self.k -= 1
                    self.logger.info('Found a link for year "{}", new_page = {}'.format(self.k,new_page))
                    yield scrapy.Request(new_page, 
                                             callback=self.parse_page, 
                                             priority = -1000, 
                                             meta={'flag':self.k})
                else:
                    while not new_page: 
                        self.logger.info('Link not found for year {}, trying with previous year {}'.format(self.k,self.k-1))
                        self.k -= 1
                        if self.k < self.year:
                            raise CloseSpider('Reached date: {}. Crawling finished'.format(self.date))
                        xpath = "//div/a[contains(@href,'time') and contains(text(),'" + str(self.k) + "')]/@href"
                        new_page = response.xpath(xpath).extract()
                    self.logger.info('Found a link for year "{}", new_page = {}'.format(self.k,new_page))
                    new_page = response.urljoin(new_page[0])
                    self.k -= 1
                    yield scrapy.Request(new_page, 
                                             callback=self.parse_page,
                                             priority = -1000,
                                             meta={'flag':self.k}) 
            else:
                    self.logger.info('Crawling has finished with no errors!')
        else:
            new_page = response.urljoin(new_page[0])
            if 'flag' in response.meta:
                self.logger.info('Page scraped, clicking on "more"! new_page = {}'.format(new_page))
                yield scrapy.Request(new_page, 
                                         callback=self.parse_page, 
                                         priority = -1000, 
                                         meta={'flag':response.meta['flag']})
            else:
                self.logger.info('First page scraped, clicking on "more"! new_page = {}'.format(new_page))
                yield scrapy.Request(new_page, 
                                         callback=self.parse_page, 
                                         priority = -1000, 
                                         meta={'flag':self.k})

    def parse_post(self, response):
        '''
        parse post does multiple things:
            1) loads replied-to-comments page one-by-one 
            2) call parse_reply on the nested comments
            3) adds simple (not-replied-to) comments
            4) goes to new comment page
        '''
        #load replied-to comments pages
       
        path = './/div[string-length(@class) = 2 and count(@id)=1 and contains("0123456789", substring(@id,1,1)) and .//div[contains(@id,"comment_replies")]]'  + '['+ str(response.meta['index']) + ']'
        group_flag = response.meta['group'] if 'group' in response.meta else None

        post_id = response.meta['post_id'] 
        current_date =response.meta['current_date'] 

        for reply in response.xpath(path):
            source = reply.xpath('.//h3/a/text()').extract()
            answer = reply.xpath('.//a[contains(@href,"repl")]/@href').extract()
            ans = response.urljoin(answer[::-1][0])
            self.logger.info('{} nested comment'.format(str(response.meta['index'])))
            yield scrapy.Request(ans,
                                 callback=self.parse_reply,
                                 priority=1000,
                                 meta={'reply_to':source,
                                       'url':response.url,
                                       'index':response.meta['index'],
                                       'flag':'init',
                                       'group':group_flag,'post_id':post_id,'current_date':current_date})
        #load regular comments     
        if not response.xpath(path): 
            path2 = './/div[string-length(@class) = 2 and count(@id)=1 and contains("0123456789", substring(@id,1,1)) and not(.//div[contains(@id,"comment_replies")])]'
            for i,reply in enumerate(response.xpath(path2)):
                self.logger.info('{} regular comment'.format(i+1))
                new = ItemLoader(item=CommentsItem(),selector=reply)
                new.context['lang'] = self.lang           
                new.add_xpath('source','.//h3/a/text()')  
                new.add_xpath('source_url','.//h3/a/@href')   
                new.add_xpath('text','.//div[h3]/div[1]//text()')
                new.add_value('reply_to','ROOT')
                new.add_xpath('reactions','.//a[contains(@href,"reaction/profile")]//text()')
                new.add_value('url',response.url)
                new.add_value('post_id',post_id)
                yield new.load_item()
            
        #new comment page
        if not response.xpath(path):
            next_xpath = './/div[contains(@id,"see_next")]'
            prev_xpath = './/div[contains(@id,"see_prev")]'
            if not response.xpath(next_xpath) or group_flag == 1:
                for next_page in response.xpath(prev_xpath):
                    new_page = next_page.xpath('.//@href').extract()
                    new_page = response.urljoin(new_page[0])
                    self.logger.info('New page to be crawled {}'.format(new_page))
                    yield scrapy.Request(new_page,
                                         callback=self.parse_post,
                                         meta={'index':1,
                                               'group':1,'post_id':post_id,'current_date':current_date})  
                    if self.date >= current_date:
                        raise CloseSpider('Reached date: {}'.format(self.date))         
            else:
                for next_page in response.xpath(next_xpath):
                    new_page = next_page.xpath('.//@href').extract()
                    new_page = response.urljoin(new_page[0])
                    self.logger.info('New page to be crawled {}'.format(new_page))
                    yield scrapy.Request(new_page,
                                         callback=self.parse_post,
                                         meta={'index':1,
                                               'group':group_flag,'post_id':post_id,'current_date':current_date})      

                    if self.date >= current_date:
                        raise CloseSpider('Reached date: {}'.format(self.date))   
        
    def parse_reply(self,response):
        '''
        parse reply to comments, root comment is added if flag
        '''

        if response.meta['flag'] == 'init':
            #parse root comment
            for root in response.xpath('//div[contains(@id,"root")]/div/div/div[count(@id)!=1 and contains("0123456789", substring(@id,1,1))]'): 
                new = ItemLoader(item=CommentsItem(),selector=root)
                new.context['lang'] = self.lang           
                new.add_xpath('source','.//h3/a/text()')  
                new.add_xpath('source_url','.//h3/a/@href') 
                new.add_value('reply_to','ROOT')
                new.add_xpath('text','.//div[1]//text()')
                new.add_xpath('reactions','.//a[contains(@href,"reaction/profile")]//text()')
                new.add_value('url',response.url)
                new.add_value('post_id',response.meta['post_id'])
                yield new.load_item()
            #parse all replies in the page
            for reply in response.xpath('//div[contains(@id,"root")]/div/div/div[count(@id)=1 and contains("0123456789", substring(@id,1,1))]'): 
                new = ItemLoader(item=CommentsItem(),selector=reply)
                new.context['lang'] = self.lang           
                new.add_xpath('source','.//h3/a/text()')  
                new.add_xpath('source_url','.//h3/a/@href') 
                new.add_value('reply_to',response.meta['reply_to'])
                new.add_xpath('text','.//div[h3]/div[1]//text()')
                new.add_xpath('reactions','.//a[contains(@href,"reaction/profile")]//text()')
                new.add_value('url',response.url)  
                new.add_value('post_id',response.meta['post_id']) 
                yield new.load_item()
                
            back = response.xpath('//div[contains(@id,"comment_replies_more_1")]/a/@href').extract()
            if back:
                self.logger.info('Back found, more nested comments')
                back_page = response.urljoin(back[0])
                yield scrapy.Request(back_page, 
                                     callback=self.parse_reply,
                                     priority = 1000,
                                     meta={'reply_to':response.meta['reply_to'],
                                           'flag':'back',
                                           'url':response.meta['url'],
                                           'index':response.meta['index'],
                                           'group':response.meta['group'],'post_id':response.meta['post_id'],'current_date':response.meta['current_date']})

            else:
                next_reply = response.meta['url']
                self.logger.info('Nested comments crawl finished, heading to proper page: {}'.format(response.meta['url']))
                yield scrapy.Request(next_reply,
                                     callback=self.parse_post,
                                     meta={'index':response.meta['index']+1,
                                           'group':response.meta['group'],'post_id':response.meta['post_id'],'current_date':response.meta['current_date']})
                
        elif response.meta['flag'] == 'back':
            #parse all comments
            for reply in response.xpath('//div[contains(@id,"root")]/div/div/div[count(@id)=1 and contains("0123456789", substring(@id,1,1))]'): 
                new = ItemLoader(item=CommentsItem(),selector=reply)
                new.context['lang'] = self.lang           
                new.add_xpath('source','.//h3/a/text()')  
                new.add_xpath('source_url','.//h3/a/@href') 
                new.add_value('reply_to',response.meta['reply_to'])
                new.add_xpath('text','.//div[h3]/div[1]//text()')
                new.add_xpath('reactions','.//a[contains(@href,"reaction/profile")]//text()')
                new.add_value('url',response.url)   
                new.add_value('post_id',response.meta['post_id'])
                yield new.load_item()
            #going backwards
            back = response.xpath('//div[contains(@id,"comment_replies_more_1")]/a/@href').extract()
            self.logger.info('Back found, more nested comments')
            if back:
                back_page = response.urljoin(back[0])
                yield scrapy.Request(back_page, 
                                     callback=self.parse_reply,
                                     priority=1000,
                                     meta={'reply_to':response.meta['reply_to'],
                                           'flag':'back',
                                           'url':response.meta['url'],
                                           'index':response.meta['index'],
                                           'group':response.meta['group'],'post_id':response.meta['post_id'],'current_date':response.meta['current_date']})

            else:
                next_reply = response.meta['url']
                self.logger.info('Nested comments crawl finished, heading to home page: {}'.format(response.meta['url']))
                yield scrapy.Request(next_reply,
                                     callback=self.parse_post,
                                     meta={'index':response.meta['index']+1,
                                           'group':response.meta['group'],'post_id':response.meta['post_id'],'current_date':response.meta['current_date']})
                
