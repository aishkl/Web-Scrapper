pip install -r requirements.txt

python run_scraper.py -email="xxxxx" -password="xxxxx" -page="xxxxx" -date="yyyy-mm-dd"

EXAMPLE :

python run_scraper.py -email="xyz@gmail.com" -password="xyz" -page="SamsungIndia" -date="2020-06-16"

email and pwd : Credentials to login to fb
page : facebook page to be scrapped(username of page)
date : date till which the data is to be scraped from the current date

OUTPUT :

Results  can be found in output folder: Facebook posts and comments are mapped with post_id.
1) fb_posts : Output file with scrapped posts.
   Scrapped data of any FB posts :
	a) post_id : ID of post
	b) source  : source page of post
	c) date	   : Date of post published
	d) text	   : Actual post text
	e) content : Any additional content of the given post
	f) Number of reactions,likes,comments,haha,wow etc.
   

2) fb_comments : Output file with scrapped comments of above posts.
		 A post have can multiple comments hence mapped with post_id.
  Scrapped data of any FB comments:
	a) post_id : ID of post of given comments
	b) source  : Source name of commentor
	c) reply_to : Replied to name of commentor (As comments are nested)
	d) text : Text comment
	e) reactions : No of reactions over comment.

 
