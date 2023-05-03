# AcadGPT

A Discord Bot for distilling papers, GitHub repos, Blogposts, and much more using the power of LLMs and vector search.

![ezgif com-video-to-gif (1)](https://user-images.githubusercontent.com/6007894/235933127-c4abb7bb-7f07-4585-8f4c-0847d6506c4d.gif)


## Getting Started

1. Create your free `Redis` datastore [here](https://redis.com/try-free/).
2. Get your `OpenAI` API key [here](https://platform.openai.com/overview).
3. Get your `ES` credentials [here](https://app.bonsai.io/signup).
4. Run the `GROBID` using the given bash script before parsing PDF.
5. Create your `Discord` bot [here](https://discord.com/login?redirect_to=%2Fdevelopers%2Fapplications).

## Setup env and install packages:

Set the required environment variables before running the script. See the `environment.py` file for reference.

```bash
conda create -n acadgpt python=3.10
```

```bash
conda activate acadgpt
```

```bash
poetry install
```

## Serving

Serve Grobid

```bash
bash serve_grobid.sh
```

Run your bot:

```bash
python acad_bot.py
```

Roadmap:

- [ ] Refactor entire code base to make it more maintainable
- [ ] Add contribution guide
- [ ] Add readthedocs page post-refactor
- [ ] Add CI/CD pipeline
- [ ] Add Pypi package
- [ ] Add docker image file and free built image on dockerhub
- [ ] Integrate with paperswithcode and connected papers' APIs
- [ ] Add latex based dense vector search
- [ ] Add voice to conversation interface
