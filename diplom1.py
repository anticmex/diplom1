import requests
import json
from pprint import pprint
import time
from tqdm import tqdm


class VkApi:
    # Класс созданный для работы с некоторыми функциями ВК через API

    def __init__(self, token):
        self.token = token
        self.params = {'access_token': token}
        self.base_url = 'https://api.vk.com/method/'

    def __main_url__(self, vk_method):
        # создание базовой URL для VK API

        return self.base_url + vk_method

    def alternative_mutual_friends_finder(self, source_uid, target_uid):
        # Попытка поиска общих друзей в случае если токен пользователя не позволяет получить доступ к просмотру
        # общих друзей запрошенных Юзеров.

        user1_friends = set(self.friends_list(source_uid, 0)['response']['items'])
        user2_friends = set(self.friends_list(target_uid, 0)['response']['items'])

        id_list = []
        for ids in user1_friends & user2_friends:
            id_list.append(ids)

        return f'Список общих друзей пользователя {source_uid} и {target_uid} следующий:\n' \
               f'{self.id_to_name_convertor(id_list)}'

    def friends_list(self, user_id, cheker=1):
        # метод определяющий список друзей пользователя(по user_id)

        self.request_friends = requests.get(
            f'{self.__main_url__("friends.get")}?user_id={user_id}&v=5.21',
            params=self.params
        )
        if cheker == 0:
            return self.request_friends.json()
        else:
            id_list = self.request_friends.json()['response']['items']

            return f'Список друзей пользователя {user_id} следующий:\n {self.id_to_name_convertor(id_list)}'

    def mutual_friends(self, source_uid, target_uid):
        # метод определяющий список общий друзей пользователя(по user_id) и пользователя чей токен применен

        self.mutual_friends = requests.get(
            f'{self.__main_url__("friends.getMutual")}'
            f'?source_uid={source_uid}&target_uid={target_uid}&v=5.21',
            params=self.params
        )

        if 'error' in self.mutual_friends.json():
            return self.alternative_mutual_friends_finder(source_uid, target_uid)
        else:
            id_list = self.mutual_friends.json()['response']
            print(id_list)
            return f'Список общих друзей пользователя {source_uid} и {target_uid} следующий:\n ' \
                   f'{self.id_to_name_convertor(id_list)}'

    def id_to_name_convertor(self, *user_id):
        # позволяет узнать человекочитаемое имя пользователя по его ID vk. и отображение в более-менее красивом виде.

        usersid_name = {}

        if isinstance(user_id[0], list):
            user_id = user_id[0]

        for id in tqdm(user_id):
            req = requests.get(
                f'https://api.vk.com/method/users.get?user_ids={id}&v=5.120',
                params={'access_token': self.token}
            )

            if not 'error' in req.json():
                usersid_name['id' + str(id)] = req.json()['response'][0]['first_name'] + \
                                               " " + \
                                               req.json()['response'][0]['last_name']

            else:
                time.sleep(4)

        return usersid_name

    def vkuser_photoget(self, *user_id):
        for id in tqdm(user_id, desc=f'Обработка страницы пользователя.'):
            photoget = requests.get(
                f'https://api.vk.com/method/photos.get?owner_id={id}&'
                f'&album_id=profile&extended=1&photo_sizes=1&v=5.77',
                params={'access_token': self.token}
            )

        return self.best_photo_get(photoget)

    def best_photo_get(self, json_request):
        output_list = []

        height = 0
        width = 0
        for i, item in enumerate(tqdm(json_request.json()['response']['items'],
                                      desc='Скачиваем фото со стены пользователя')):
            for size in item['sizes']:
                if size['height'] > height or size['width'] > width:
                    height = size['height']
                    width = size['width']
                    url = size['url']
            output_dict = {
                'position': i + 1,
                'name': str(item['likes']['count'] + item['likes']['user_likes']) + '_' + str(item['date']),
                'url': url,
                'height': height,
                'width': width

            }

            output_list.append(output_dict)
        return output_list


class Yaload:

    def __init__(self, token):
        self.BASE_URL = 'https://cloud-api.yandex.net:443'
        self.token = token

        self.AUTHOR = {"Authorization": token}
        self.BAS_STRUCTURE_URL = '/v1/disk/resources'
        self.BASE_UPLOAD_URL = self.BAS_STRUCTURE_URL + '/upload'
        self.DISK_ROOT = {'path': '/'}

    def get_filename_from_path(self, file_name):

        for i, word in enumerate(reversed(file_name)):
            if word == '/':
                break
        return file_name[len(file_name) - i:]

    def folder_selection(self, json_list):
        folder_list = []
        for items in json_list['_embedded']['items']:
            if not "." in items['name']:
                folder_list.append(items["name"])
        print("Желаете указать папку для загрузки файла?")
        print(f'Текущие папки на диске:\n{folder_list}')
        question_to_user = \
            input("'y'- да, выбрать; 'n' - нет, загрузить в корень; 'иное' - создать временную папку для загрузки.")
        if question_to_user == 'y':
            folder_name = input("Укажите название папки: ")
        elif question_to_user == 'n':
            folder_name = ''
        else:
            folder_name = 'Временная/'
        return folder_name

    # def files_select(self, file_full_path):
    #
    #     self.full_path_filename = file_full_path
    #     filename = self.get_filename_from_path(self.full_path_filename)
    #     return filename

    def loading_process(self, list_of_dictions):

        statistic_list = []

        # запрос списка папок на Ядиске
        disk_folders_request = requests.get(self.BASE_URL + self.BAS_STRUCTURE_URL,
                                            params=self.DISK_ROOT, headers=self.AUTHOR)
        # выбор папки на Ядиске
        self.disk_folder_upload_name = "/" + self.folder_selection(disk_folders_request.json())
        print(f'Выбрана папка для загрузки: "{self.disk_folder_upload_name}"')

        for ldict in tqdm(list_of_dictions, desc='Загрузка файлов на Ядиск'):
            statistic_data = {}
            uploading_filename = str(ldict['position']) + "_" + ldict['name']
            uploading_fileurl = ldict['url']

            self.upload_file(self.disk_folder_upload_name, uploading_fileurl, uploading_filename)
            statistic_data['file_name'] = uploading_filename
            statistic_data['size'] = str(ldict['height']) + "x" + str(ldict['width'])
            statistic_list.append(statistic_data)

        return self.statistic_upload(self.disk_folder_upload_name, statistic_list)

    def upload_file(self, upload_folder, file_url, file_name):

        # создание пути на Ядиске для загрузки файла (тут можно переименовывать файлы)
        disk_pre_upload_params = {'path': upload_folder + file_name + ".jpg", 'overwrite': 'true'}

        # операция с загружаемым файлом
        quickload = requests.get(file_url)
        files = {'file': quickload.content}

        # создание ссылки для загрузки на Ядиск (в соответствии с требованиями Я API)
        pre_upload_url = requests.get(self.BASE_URL + self.BASE_UPLOAD_URL, headers=self.AUTHOR,
                                      params=disk_pre_upload_params)

        # процесс загрузки
        upload = requests.put(pre_upload_url.json()['href'], headers=self.AUTHOR, files=files)
        if upload.status_code < 400:
            return f"Файл {file_name} успешно загружен!"
        else:
            return "Что-то пошло не так!"

    def statistic_upload(self, upload_folder, data_list):

        disk_pre_upload_params = {'path': upload_folder + "statistic.json", 'overwrite': 'true'}
        pre_upload_url = requests.get(self.BASE_URL + self.BASE_UPLOAD_URL, headers=self.AUTHOR,
                                      params=disk_pre_upload_params)

        with open("statistic.json", "w"):
            files = {'file': json.dumps(data_list)}

        return requests.put(pre_upload_url.json()['href'], headers=self.AUTHOR, files=files)


def main():
    vktoken = input("Введите токен для работы с VK: ")
    yatoken = input("Введите токен для работы с Яндекс-диском: ")
    vk_user_id = input("Укажите id пользователя ВК для загрузки фото: ")


    photo_listofdicts = VkApi(vktoken).vkuser_photoget(vk_user_id)
    if len(photo_listofdicts) > 0:
        Yaload(yatoken).loading_process(photo_listofdicts)
        print("Успешное завершение работы!")

    else:
        print("Не удалось обнаружить фото на странице или")
        print("отсутствует доступ к странице пользователя.")

main()

