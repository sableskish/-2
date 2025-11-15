import argparse
import sys
import os
import urllib.request
import urllib.error
from urllib.parse import urlparse
import re
import gzip
import tempfile


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
                    errors.append(f"некорректный URL: {self.repository_url}")
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


class AlpinePackageManager:
    
    def __init__(self, repository_url):
        self.repository_url = repository_url.rstrip('/')
        self.packages_cache = {}
    
    def fetch_index_file(self, arch='x86_64', branch='v3.18'):
        try:
            index_url = f"{self.repository_url}/{branch}/main/{arch}/APKINDEX.tar.gz"
            print(f"загрузка индексного файла: {index_url}")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz') as temp_file:
                temp_path = temp_file.name
            
            try:
                urllib.request.urlretrieve(index_url, temp_path)
                
                with gzip.open(temp_path, 'rb') as gz_file:
                    content = gz_file.read().decode('utf-8', errors='ignore')
                
                return self.parse_apkindex(content)
                
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except urllib.error.URLError as e:
            raise Exception(f"ошибка загрузки индексного файла: {e}")
        except Exception as e:
            raise Exception(f"ошибка обработки индексного файла: {e}")
    
    def parse_apkindex(self, content):
        packages = {}
        current_pkg = {}
        
        for line in content.split('\n'):
            if line.startswith('C:'):
                if current_pkg and 'P' in current_pkg and 'V' in current_pkg:
                    pkg_name = current_pkg['P']
                    packages[pkg_name] = {
                        'name': pkg_name,
                        'version': current_pkg['V'],
                        'description': current_pkg.get('T', ''),
                        'dependencies': self.parse_dependencies(current_pkg.get('D', '')),
                        'provides': current_pkg.get('p', '').split(),
                        'checksum': current_pkg.get('C', '')
                    }
                current_pkg = {}
            
            if ':' in line:
                key, value = line.split(':', 1)
                current_pkg[key] = value.strip()
        
        if current_pkg and 'P' in current_pkg and 'V' in current_pkg:
            pkg_name = current_pkg['P']
            packages[pkg_name] = {
                'name': pkg_name,
                'version': current_pkg['V'],
                'description': current_pkg.get('T', ''),
                'dependencies': self.parse_dependencies(current_pkg.get('D', '')),
                'provides': current_pkg.get('p', '').split(),
                'checksum': current_pkg.get('C', '')
            }
        
        return packages
    
    def parse_dependencies(self, deps_string):
        if not deps_string:
            return []
        
        dependencies = []
        return dependencies
    
    def get_package_dependencies(self, package_name, package_version=None):
        if not self.packages_cache:
            self.packages_cache = self.fetch_index_file()
        
        if package_name not in self.packages_cache:
            raise Exception(f"пакет '{package_name}' не найден в репозитории")
        
        package_info = self.packages_cache[package_name]
        
        if package_version and package_info['version'] != package_version:
            matching_packages = []
            for pkg_name, pkg_info in self.packages_cache.items():
                if pkg_name == package_name and pkg_info['version'] == package_version:
                    matching_packages.append(pkg_info)
            
            if not matching_packages:
                raise Exception(f"пакет '{package_name}' версии '{package_version}' не найден")
            package_info = matching_packages[0]
        
        return package_info['dependencies']
    
    def display_dependencies(self, package_name, package_version=None, filter_substring=None):
        try:
            dependencies = self.get_package_dependencies(package_name, package_version)
            
            if filter_substring:
                dependencies = [dep for dep in dependencies if filter_substring.lower() in dep.lower()]
            
            print(f"ПРЯМЫЕ ЗАВИСИМОСТИ ПАКЕТА: {package_name}")
            if package_version:
                print(f"ВЕРСИЯ: {package_version}")
            if filter_substring:
            
            if not dependencies:
                print("зависимости не найдены")
            else:
                for i, dep in enumerate(sorted(dependencies), 1):
                    print(f"{i:2d}. {dep}")
            
            print(f"{'='*60}")
            print(f"всего зависимостей: {len(dependencies)}")
            
            return dependencies
            
        except Exception as e:
            print(f"ошибка при получении зависимостей: {e}", file=sys.stderr)
            return []


def parse_arguments():
    parser = argparse.ArgumentParser
    
    parser.add_argument(
        '--package',
        '--package-name',
        dest='package_name',
        required=True,
    )
    
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        '--repo-url',
        '--repository-url',
        dest='repository_url',
    )
    source_group.add_argument(
        '--test-repo',
        '--test-repository',
        dest='test_repo_path',
    )
    
    parser.add_argument(
        '--mode',
        '--work-mode',
        dest='work_mode',
        choices=['online', 'offline', 'test'],
        default='online',
    )
    
    parser.add_argument(
        '--version',
        '--package-version',
        dest='package_version',
    )
    
    parser.add_argument(
        '--output',
        '--output-file',
        dest='output_filename',
        default='dependency_graph.png',
    )
    
    parser.add_argument(
        '--filter',
        '--filter-substring',
        dest='filter_substring',
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
        
        if config.repository_url:
            print(f"\nзагрузка информации о пакете {config.package_name}...")
            
            package_manager = AlpinePackageManager(config.repository_url)
            
            dependencies = package_manager.display_dependencies(
                config.package_name,
                config.package_version,
                config.filter_substring
            )
            
            print(f"\n сбор данных завершен. найдено {len(dependencies)} зависимостей.")
            
        elif config.test_repo_path:
            print(f"\n режим тестового репозитория: {config.test_repo_path}")
            print("для этапа 2 требуется URL репозитория Alpine Linux")
        
    except argparse.ArgumentError as e:
        print(f"ошибка в аргументах командной строки: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nпрограмма прервана пользователем", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()