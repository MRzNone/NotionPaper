#!/usr/bin/env python
# coding: utf-8

# In[1]:

import json
import requests
import arxiv
from collections import defaultdict
import numpy as np
from multiprocessing.pool import ThreadPool

# In[2]:

secret = 'secret_kUZyO5ppcfCAdTomWG96yxx4KhhESaD1tVn99nHxwFr'

databaseId = 'b2e7bcbfb6bd4e8cb0116f5163551700'

headers = {
    "Accept": "application/json",
    "Notion-Version": "2022-02-22",
    "Content-Type": "application/json",
    "Authorization": F"Bearer {secret}",
}

# In[3]:

url = F"https://api.notion.com/v1/databases/{databaseId}/query"

res = requests.request('POST', url, headers=headers)
res = json.loads(res.text)

# In[4]:

existing_titles = [
    r['properties']['Name']['title'][0]['plain_text'] for r in res['results']
    if len(r['properties']['Name']['title']) > 0
]

# In[5]:

# Query database format
url = F"https://api.notion.com/v1/databases/{databaseId}"

res = requests.request('GET', url, headers=headers)
res = json.loads(res.text)

# In[6]:

link_proto = res['properties']['Link'].copy()
date_proto = res['properties']['Date'].copy()
tags_proto = res['properties']['Tags'].copy()
src_proto = res['properties']['Source'].copy()

# In[7]:


def make_title(title):
    return {
        "Name": {
            "title": [{
                "type": "text",
                "text": {
                    "content": str(title)
                }
            }]
        }
    }


# In[8]:


def make_url(proto, url):
    return {
        proto['id']: {
            'type': 'url',
            'url': str(url),
        }
    }


# In[9]:


def make_text(proto, text):
    return {
        proto['id']: {
            'rich_text': [{
                'type': 'text',
                'text': {
                    'content': str(text)
                }
            }]
        }
    }


# In[10]:


def extract_options(proto):
    m_options = {
        dic['name'].lower(): dic['id']
        for dic in proto['multi_select']['options']
    }
    options = defaultdict(lambda: None)
    options.update(m_options)

    return options


# In[11]:


def make_multi_sel(proto, sel):
    options = extract_options(proto)

    sel = [options[s.lower()] for s in sel]
    sel = list(set(sel))
    if None in sel:
        sel.remove(None)

    return {proto['id']: {'multi_select': [{'id': sel_id} for sel_id in sel]}}


# In[12]:


def create_page(properties={}):
    url = F"https://api.notion.com/v1/pages"

    payload = {
        'parent': {
            'type': 'database_id',
            'database_id': databaseId,
        },
        'properties': properties
    }

    res = requests.request('POST', url, headers=headers, json=payload)
    res = json.loads(res.text)

    return res['id']


# In[13]:


def find_lonest_common(str1, str2):
    len1 = len(str1)
    len2 = len(str2)

    # dp[i][j] if the lonest commonsuffix of 0...i in str1 and 0...j in str2
    dp = [[0 for _ in range(len2)] for _ in range(len1)]

    for i in range(len1):
        for j in range(len2):
            res = 0

            # check common
            if str1[i] == str2[j]:
                res += 1

            # check prev
            if i > 0 and j > 0:
                res += dp[i - 1][j - 1]

            dp[i][j] = res

    dp = np.array(dp)

    i, j = np.unravel_index(dp.argmax(), dp.shape)
    len_common = dp[i, j]

    common_str = str2[j - len_common + 1:j + 1]

    # check before and after non-str
    check = True

    if i - len_common >= 0:
        if str1[i - len_common].isalpha():
            check = False

    if i + 1 < len1:
        if str1[i + 1].isalpha():
            check = False

    return common_str, check


# In[14]:


def get_paper_info(arxiv_url):
    arxiv_id = arxiv_url.split('/')[-1]

    res = next(arxiv.Search(id_list=[arxiv_id]).results())

    title = res.title
    link = res.entry_id
    date = res.updated.year

    # extract tags
    src = []
    if res.comment is not None:
        comment = res.comment.lower()
        src_options = extract_options(src_proto)
        src = [find_lonest_common(comment, opt) for opt in src_options]
        src = [t_src for t_src, check in src if check]

    return title, link, date, src


# In[15]:


def promt_for_tags():
    tags_options = list(extract_options(tags_proto))
    nums = np.arange(len(tags_options))

    opt_dict = defaultdict(lambda: None)
    opt_dict.update(dict(zip(nums, tags_options)))

    prompt = '\n'.join(F"{k:>2}: {v}" for k, v in opt_dict.items())

    print(prompt)
    print("\nChoose, separate by space")
    choices = input()
    choices = [opt_dict[int(c)] for c in choices.split() if c.isdigit()]

    choices = list(set(choices))

    if None in choices:
        choices.remove(None)

    return choices


# In[16]:


def deal_paper():
    with ThreadPool(processes=1) as pool:
        print('\n', '=' * 30)
        url = input("Paper url: ")
        async_result = pool.apply_async(get_paper_info,
                                        (url, ))  # tuple of args for foo

        choices = promt_for_tags()

        title, link, date, src = async_result.get(timeout=2)

        # check if exists
        for tt in existing_titles:
            if title in tt:
                print(F"\"{title}\" exists. Skipped")
                return

        print(F"""
>>>DETAILS:
Title:   {title}
Link:    {link}
Date:    {date}
Souces:  {', '.join(src)}
Choices: {', '.join(choices)}
        """)

        properties = {}

        properties.update(make_title(title))
        properties.update(make_url(link_proto, link))
        properties.update(make_text(date_proto, date))
        properties.update(make_multi_sel(tags_proto, choices))
        properties.update(make_multi_sel(src_proto, src))

        page_id = create_page(properties)
        print('Success!!!!')


# In[ ]:

while True:

    try:
        deal_paper()

    except TimeoutError as e:
        print("Problem getting the link")
    except Exception as e:
        print(e)

# In[ ]:
