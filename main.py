# imports
import os
import json
import uuid
import cloudscraper
from bs4 import BeautifulSoup as bs


def get_actor_pairings(soup):
    actors = []

    container = soup.find('div', class_='container')
    for row in container.select('div[class*=row ]'):
        actor = {}

        # get name
        name = row.find('h3', class_='matchuph3').text
        actor['name'] = name

        # get gender
        pic = row.find('a', target='_parent').get('href')
        actor['gender'] = 'f' if 'gender=f' in pic else 'm'

        # get movie names and urls
        movies = []
        for item in row.findAll('li'):
            movies.append({
                'name': item.text,
                'url': 'https://www.iafd.com/' + item.find('a').attrs.get('href')
            })
        actor['movies'] = movies

        # get num of scene pairings
        actor['num_scenes_together'] = len(movies)

        # add to actor list
        actors.append(actor)

    return actors


def subset_actors_to_gender(actors, gender):
    tmp = []
    for actor in actors:
        if actor.get('gender') == gender:
            tmp.append(actor)

    return tmp


def subset_actors_to_min_num_pairings(actors, min_num_scenes):
    tmp = []
    for actor in actors:
        if actor.get('num_scenes_together') >= min_num_scenes:
            tmp.append(actor)

    return tmp


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # set actor page url (find on iafd)
    actor_name = 'Jenner'
    actor_page_url = 'https://www.iafd.com/matchups.rme/perfid=jenner/gender=m'
    output_folder = r'C:\Users\Lewis\Desktop\pairings'

    # init web scraper and get content
    scraper = cloudscraper.create_scraper()
    request = scraper.get(actor_page_url)
    soup = bs(request.content, 'html.parser')

    # get all movies where pair detected
    actors = get_actor_pairings(soup)

    # subset to pairings with men/women/both (leave empty)
    gender = 'm'
    if gender in ['f', 'm']:
        actors = subset_actors_to_gender(actors, gender)

    # subset to min number of scenes together
    min_num_scenes = 1
    actors = subset_actors_to_min_num_pairings(actors, min_num_scenes)

    # iterate movie pages and extract acts, scenes
    for actor in actors:

        for movie in actor.get('movies'):
            movie['main_actor'] = actor_name
            movie['pair_actor'] = actor.get('name')
            movie['cast'] = []
            movie['acts'] = []

            # get current page content via bs
            request = scraper.get(movie.get('url'))
            soup = bs(request.content, 'html.parser')

            # get scene info
            if soup.find(id='sceneinfo') is not None:
                for scene in soup.find(id='sceneinfo').findAll('li'):

                    scene = scene.text
                    if actor.get('name') in scene and actor_name in scene:

                        # split scene strings by comma, remove scene part
                        scene_actors = scene.split(',')
                        scene_actors[0] = scene_actors[0].split('.')[1]
                        scene_actors = [e.strip() for e in scene_actors]

                        for scene_actor in scene_actors:
                            if scene_actor not in movie['cast']:
                                movie['cast'].append(scene_actor)
                                movie['cast'].sort()

                        # loop castbox if exists and get all acts
                        if soup.find_all('div', class_='castbox') is not None:
                            for castbox in soup.find_all('div', class_='castbox'):

                                # get all acts for all actors in scene
                                castbox_name = castbox.find('a').text
                                if castbox_name in scene_actors:

                                    castbox_parts = castbox.text.split(')')
                                    castbox_text = castbox_parts[1] if len(castbox_parts) > 1 else castbox_parts[0]
                                    castbox_text = castbox_text.replace(castbox_name, '')
                                    castbox_text = castbox_text.strip()

                                    if castbox_text is not None and castbox_text != '':
                                        castbox_acts = castbox_text.split(' ')
                                        castbox_acts = [e.strip() for e in castbox_acts]

                                        for act in castbox_acts:
                                            if act not in movie['acts']:
                                                movie['acts'].append(act)
                                                movie['acts'].sort()

            # create actor folder if not already
            out_actor_folder = os.path.join(output_folder, actor_name)
            if not os.path.exists(out_actor_folder):
                os.mkdir(out_actor_folder)

            # create unique id for json file
            output_file = str(uuid.uuid4()) + '.json'
            with open(os.path.join(out_actor_folder, output_file), 'w') as file:
                json.dump(movie, file)

