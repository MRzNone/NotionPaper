# NotionPaper

Import paper info into notion with python.

Notion page [example](https://weihaoz.notion.site/b2e7bcbfb6bd4e8cb0116f5163551700). You can create template from this page.

![demo](demo.GIF)

# Get started

You will need a secret to authenticate access to Notion, and the database ID for the table.

## Notion Authentication

Follow [this](https://developers.notion.com/docs) to generate a notion secret.

- Create a Notion integration.
- Share your database page with the integration.
- Replace `secret` in the code.

```
secret = 'secret_kUZyO5ppcfCAdTomWG96yxx4KhhESaD1tVn99nHxwFr'
```

## Link to Database

Replace `databaseId` in the code.

```
https://www.notion.so/myworkspace/a8aec43384f447ed84390e8e42c2e089?v=...
                                  |--------- Database ID --------|
```

## Install dependencies

`pip install arxiv numpy`

## Run the code

`python Notion_paper.py`

# Development

Useful resources:

- https://prettystatic.com/notion-api-python/
- https://developers.notion.com/reference/intro
