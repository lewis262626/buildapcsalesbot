import praw
import sqlite3
import os
import re

DBNAME = 'posts.db'

def setupPRAW():
    user_agent = "Linux: Reddit buildapcsalesuk bot: version 71986d20d9aec (by: "
    reddit = praw.Reddit(client_id='', 
                        client_secret='',
                        user_agent=user_agent)

    subreddit = reddit.subreddit('buildapcsalesuk')
    print('Using subreddit: {0}\n'.format(subreddit.title))

    return reddit

def setupDB():
    isNotThere = not os.path.exists(DBNAME)
    if isNotThere:
        conn = sqlite3.connect(DBNAME)
        print('Executing schema\n')
        c = conn.cursor()
        c.execute('''CREATE TABLE post (postid text NOT NULL PRIMARY KEY, link text)''')
        c.execute('''CREATE TABLE contents (score integer, user text, price text, title text NOT NULL, postid text NOT NULL, PRIMARY KEY(postid, title))''')
        conn.commit()
    else:
        print('Database is already setup\n')

    conn = sqlite3.connect(DBNAME)
    return conn

def get_submissions(reddit):
    submissions = []
    for submission in reddit.subreddit('buildapcsalesuk').new(limit=None):
        dataDic = getDataAboutPost(submission)
        submissions.append(dataDic)

    return submissions


def getDataAboutPost(submission):
    data ={}
    data['price'] = getPrice(submission.title)
    data['title'] = submission.title
    data['score'] = submission.score
    data['id']    = submission.id
    data['link']   = submission.url
    data['user']  = str(submission.author)
    
    return data

def getPrice(title):
    matches = re.search('£(\d+(\.|,)\d{1,2})|£(\d)+', title)
    if matches == None:
        return "N/A"
    else:
        return matches.group()

def insertData(submissions, conn):
    c = conn.cursor()
    for submission in submissions:
        if not isDuplicate(submission, conn):
            c.execute('''INSERT INTO post VALUES(?,?)''', (submission['id'], submission['link']))
            c.execute('''INSERT INTO contents VALUES(?,?,?,?,?)''', (submission['score'], submission['user'], submission['price'], submission['title'], submission['id']))
            conn.commit()
        else:
            updatePost(submission, conn)

def isDuplicate(submission, conn):
    c = conn.cursor()
    c.execute('''SELECT postid from post''')
    all_rows = c.fetchall()
    for row in all_rows:
        if submission['id'] == row[0]:
            return True

    return False

def updatePost(submission, conn):
    score = (submission['score'], submission['id'])
    
    c = conn.cursor()
    c.execute('''UPDATE contents SET score = ? WHERE postid = ?''', score)
    conn.commit()



if __name__ == "__main__":
    print('Executing again')
    reddit = setupPRAW()
    conn = setupDB()
    posts = get_submissions(reddit)
    insertData(posts, conn)
    conn.close()
