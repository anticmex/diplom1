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

    def vk_user_photo_get(self, *user_id):
        for id in tqdm(user_id, desc=f'Обработка страницы пользователя.'):
            photo_get = requests.get(
                f'https://api.vk.com/method/photos.get?owner_id={id}&'
                f'&album_id=profile&extended=1&photo_sizes=1&v=5.77',
                params={'access_token': self.token}
            )
        if 'error' in photo_get.json():

            return 0
        else:
            return self.best_photo_get(photo_get)

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
            folder_name = f'{input("Укажите название папки: ")}/'
            if not folder_name in items['name']:
                print(f"Создаем папку {folder_name}.")
                requests.put(self.BASE_URL + self.BAS_STRUCTURE_URL,
                             params={'path': folder_name}, headers=self.AUTHOR)
        elif question_to_user == 'n':
            folder_name = ''
        else:
            folder_name = 'Временная/'

        return folder_name


    def loading_process(self, list_of_dictions):

        statistic_list = []

        # запрос списка папок на Ядиске
        disk_folders_request = requests.get(self.BASE_URL + self.BAS_STRUCTURE_URL,
                                            params=self.DISK_ROOT, headers=self.AUTHOR)
        # выбор папки на Ядиске
        self.disk_folder_upload_name = "/" + self.folder_selection(disk_folders_request.json())
        print(f'Выбрана папка для загрузки: "{self.disk_folder_upload_name}"')

        for list_of_dicts in tqdm(list_of_dictions, desc='Загрузка файлов на Ядиск'):
            statistic_data = {}
            uploading_filename = str(list_of_dicts['position']) + "_" + list_of_dicts['name']
            uploading_file_url = list_of_dicts['url']

            self.upload_file(self.disk_folder_upload_name, uploading_file_url, uploading_filename)
            statistic_data['file_name'] = uploading_filename
            statistic_data['size'] = str(list_of_dicts['height']) + "x" + str(list_of_dicts['width'])
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
    vk_token = input("Введите токен для работы с VK: ")
    ya_token = input("Введите токен для работы с Яндекс-диском: ")
    vk_user_id = input("Укажите id пользователя ВК для загрузки фото: ")


    photo_list_of_dicts = VkApi(vk_token).vk_user_photo_get(vk_user_id)

    if photo_list_of_dicts != 0:
        Yaload(ya_token).loading_process(photo_list_of_dicts)
        print("Успешное завершение работы!")

    else:
        print("Не удалось обнаружить фото на странице или")
        print("отсутствует доступ к странице пользователя.")

main()

