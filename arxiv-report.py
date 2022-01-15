#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Project :arxiv-nlp-report 
@File    :arxiv-report.py
@Author  :JackHCC
@Date    :2022/1/14 11:40 
@Desc    :Arxiv NLP Paper Reporter

'''

import datetime
import requests
import json
import arxiv
import re

base_url = "https://arxiv.paperswithcode.com/api/v0/papers/"


def del_unicode(string):
    string = re.sub(r'\\u.{4}', '', string.__repr__())
    return string


def del_not_english(string):
    string = re.sub('[^A-Za-z]', '', string.__str__())
    return string


def get_authors(authors, first_author=False):
    output = str()
    if first_author == False:
        output = ", ".join(str(author) for author in authors)
    else:
        output = authors[0]
    return output


def sort_papers(papers):
    output = dict()
    keys = list(papers.keys())
    keys.sort(reverse=True)
    for key in keys:
        output[key] = papers[key]
    return output


def get_daily_papers(topic, query="nlp", max_results=2):
    """
    @param topic: str
    @param query: str
    @return paper_with_code: dict
    """

    # output
    content = dict()
    content_to_web = dict()

    # content
    output = dict()

    search_engine = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    cnt = 0

    for result in search_engine.results():

        paper_id = result.get_short_id()
        paper_title = result.title
        paper_url = result.entry_id

        code_url = base_url + paper_id
        paper_abstract = result.summary.replace("\n", " ")
        paper_authors = get_authors(result.authors)
        paper_first_author = get_authors(result.authors, first_author=True)
        primary_category = result.primary_category

        publish_time = result.published.date()
        update_time = result.updated.date()

        print("Time = ", update_time,
              " title = ", paper_title,
              " author = ", paper_first_author)

        # eg: 2108.09112v1 -> 2108.09112
        ver_pos = paper_id.find('v')
        if ver_pos == -1:
            paper_key = paper_id
        else:
            paper_key = paper_id[0:ver_pos]

        try:
            r = requests.get(code_url).json()
            # source code link
            if "official" in r and r["official"]:
                cnt += 1
                repo_url = r["official"]["url"]
                content[
                    paper_key] = f"|**{update_time}**|**{paper_title}**|{paper_first_author} et.al.|[{paper_id}]({paper_url})|**[link]({repo_url})**|\n"
                content_to_web[
                    paper_key] = f"- **{update_time}**, **{paper_title}**, {paper_first_author} et.al., [PDF:{paper_id}]({paper_url}), **[code]({repo_url})**\n"
            else:
                content[
                    paper_key] = f"|**{update_time}**|**{paper_title}**|{paper_first_author} et.al.|[{paper_id}]({paper_url})|null|\n"
                content_to_web[
                    paper_key] = f"- **{update_time}**, **{paper_title}**, {paper_first_author} et.al., [PDF:{paper_id}]({paper_url})\n"

        except Exception as e:
            print(f"exception: {e} with id: {paper_key}")

    data = {topic: content}
    data_web = {topic: content_to_web}
    return data, data_web


def update_json_file(filename, data_all):
    with open(filename, "r") as f:
        content = f.read()
        if not content:
            m = {}
        else:
            m = json.loads(content)

    json_data = m.copy()

    # update papers in each keywords
    for data in data_all:
        for keyword in data.keys():
            papers = data[keyword]

            if keyword in json_data.keys():
                json_data[keyword].update(papers)
            else:
                json_data[keyword] = papers

    with open(filename, "w") as f:
        json.dump(json_data, f)


def json_to_md(filename, to_web=False):
    """
    @param filename: str
    @return None
    """

    DateNow = datetime.date.today()
    DateNow = str(DateNow)
    DateNow = DateNow.replace('-', '.')

    with open(filename, "r") as f:
        content = f.read()
        if not content:
            data = {}
        else:
            data = json.loads(content)

    if to_web == False:
        md_filename = "README.md"
    else:
        md_filename = "./docs/index.md"

        # clean README.md if daily already exist else create it
    with open(md_filename, "w+") as f:
        pass

    # write data into README.md
    with open(md_filename, "a+", encoding='utf-8') as f:

        if to_web == True:
            f.write("---\n" + "layout: default\n" + "---\n\n")

        f.write("## Updated on " + DateNow + "\n\n")

        for keyword in data.keys():
            day_content = data[keyword]
            if not day_content:
                continue
            # the head of each part
            f.write(f"## {keyword}\n\n")

            if to_web == False:
                f.write("|Publish Date|Title|Authors|PDF|Code|\n" + "|---|---|---|---|---|\n")
            else:
                f.write("| Publish Date | Title | Authors | PDF | Code |\n")
                f.write("|:---------|:-----------------------|:---------|:------|:------|\n")

            # sort papers by date
            day_content = sort_papers(day_content)

            for _, v in day_content.items():
                if v is not None:
                    f.write(v)

            f.write(f"\n")

    print("finished")


if __name__ == "__main__":
    data_collector = []
    data_collector_web = []

    keywords = dict()
    keywords["NLP"] = "NLP" + "OR" + "\"Natural Language Processing\""
    keywords["Sequence Annotation"] = "\"Sequence Annotation\"OR\"Sequence Marking\""
    keywords["Named Entity Recognition"] = "\"Named Entity Recognition\""
    keywords["Text Classification"] = "\"Text Classification\"OR\"Topic Labeling\"OR\"News Classification\"OR\"Dialog Act Classification\"OR\"Natural Language Inference\"OR\"Relation Classification\"OR\"Event Prediction\""
    keywords["Sentiment Analysis"] = "\"Sentiment Analysis\""
    keywords["Question Answering"] = "\"QA\"OR\"Question Answering\""
    keywords["Information Extraction"] = "\"Information Extraction\"OR\"Automatic Summary\"OR\"Title Generation\"OR\"Event Extraction\""
    keywords["Recommendation System"] = "\"Recommendation System\"OR\"Semantic Matching\"OR\"Chatbots\""
    keywords["Knowledge Graph"] = "\"Knowledge Graph\"OR\"Knowledge Graphs\""
    keywords["GNN"] = "GNN" + "OR" + "\"Graph Neural Network\""

    for topic, keyword in keywords.items():
        # topic = keyword.replace("\"","")
        print("Keyword: " + topic)

        data, data_web = get_daily_papers(topic, query=keyword, max_results=10)
        data_collector.append(data)
        data_collector_web.append(data_web)

        print("\n")

    # update README.md file
    json_file = "nlp-arxiv-daily.json"
    #     if ~os.path.exists(json_file):
    #         with open(json_file,'w')as a:
    #             print("create " + json_file)

    # update json data
    update_json_file(json_file, data_collector)
    # json data to markdown
    json_to_md(json_file)

    # update docs/index.md file
    json_file = "./docs/nlp-arxiv-daily-web.json"
    #     if ~os.path.exists(json_file):
    #         with open(json_file,'w')as a:
    #             print("create " + json_file)

    # update json data
    update_json_file(json_file, data_collector)
    # json data to markdown
    json_to_md(json_file, to_web=True)
