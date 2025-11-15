import argparse
import sys
import os
from urllib.parse import urlparse


class ConfDependGraph:
    
    def __init__(self):
        self.package_name = None
        self.repository_url = None
        self.test_repo_path = None
        self.work_mode = None
        self.package_version = None
        self.output_filename = None
        self.filter_substring = None
    
    def validate(self):
        errors = []
        
        if not self.package_name:
            errors.append("безымЯнный пакет")
        
        if not self.repository_url and not self.test_repo_path:
            errors.append("нет URL репозитория или пути к тестовому репозиторию")
        
        if self.repository_url and self.test_repo_path:
            errors.append("два источника")
        
        if self.repository_url:
            try:
                result = urlparse(self.repository_url)
                if not all([result.scheme, result.netloc]):
                    errors.append("некорректный URL: {self.repository_url}")
            except Exception as e:
                errors.append(f"ошибка парсинга URL: {e}")
        
        if self.test_repo_path and not os.path.exists(self.test_repo_path):
            errors.append(f"файл не существует: {self.test_repo_path}")
        
        valid_modes = ['online', 'offline', 'test']
        if self.work_mode and self.work_mode not in valid_modes:
            errors.append(f"недопустимый режим. допустимые значения: {', '.join(valid_modes)}")
        
        return errors
    
    def display_config(self):
        config_data = {
            "имя анализируемого пакета": self.package_name or "не указано",
            "URL репозитория": self.repository_url or "не указано",
            "путь к тестовому репозиторию": self.test_repo_path or "не указано",
            "режим работы": self.work_mode or "не указано",
            "версия пакета": self.package_version or "не указано",
            "имя выходного файла": self.output_filename or "не указано",
            "подстрока для фильтрации": self.filter_substring or "не указано"
        }
        
        print("ТЕКУЩАЯ КОНФИГУРАЦИЯ:")
        for key, value in config_data.items():
            print(f"{key}: {value}")


def parse_arguments():
    parser = argparse.ArgumentParser(
    )
    
    parser.add_argument(
        '--package',
        '--package-name',
        dest='package_name',
        required=True,
        #имя анализируемого пакета
    )
    
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        '--repo-url',
        '--repository-url',
        dest='repository_url',
        #URL-адрес репозитория пакетов
    )
    source_group.add_argument(
        '--test-repo',
        '--test-repository',
        dest='test_repo_path',
        #путь к файлу тестового репозитория
    )
    
    parser.add_argument(
        '--mode',
        '--work-mode',
        dest='work_mode',
        choices=['online', 'offline', 'test'],
        default='online',
        #режим работы с репозиторием
    )
    
    parser.add_argument(
        '--version',
        '--package-version',
        dest='package_version',
        #версия анализируемого пакета
    )
    
    parser.add_argument(
        '--output',
        '--output-file',
        dest='output_filename',
        default='dependency_graph.png',
        #имя сгенерированного файла с изображением графа
    )
    
    parser.add_argument(
        '--filter',
        '--filter-substring',
        dest='filter_substring',
        #подстрока для фильтрации пакетов
    )
    
    return parser.parse_args()


def create_config_from_args(args):
    config = ConfDependGraph()
    
    config.package_name = args.package_name
    config.repository_url = args.repository_url
    config.test_repo_path = args.test_repo_path
    config.work_mode = args.work_mode
    config.package_version = args.package_version
    config.output_filename = args.output_filename
    config.filter_substring = args.filter_substring
    
    return config


def main():
    try:
        args = parse_arguments()
        config = create_config_from_args(args)
        validation_errors = config.validate()
        
        if validation_errors:
            print("ошибки конфигурации:", file=sys.stderr)
            for error in validation_errors:
                print(f"  - {error}", file=sys.stderr)
            sys.exit(1)
        
        config.display_config()
        
        # тут будет основная логика анализа зависимостей
        print(f"\n анализ зависимостей для пакета: {config.package_name}")
        print("режим работы:", config.work_mode)
        print("выходной файл:", config.output_filename)
        
    except argparse.ArgumentError as e:
        print(f"ошибка в аргументах командной строки: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nпрограмма прервана пользователем", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"какая-то ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()