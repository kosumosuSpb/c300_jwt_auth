"""
Ручное создание CRUD-прав по списку имён для этих прав.
Требует файл с этими правами, в котором они перечислены:

crm_button
automation
automation_sims
...

и т.д.

Запускается через

    python script_slugs_to_permissions.py

по-умолчанию имя файла - './slugs', но можно задать своё и прописать его при запуске:

    python script_slugs_to_permissions.py filename

"""

import sys

from apps.authorization.models.permissions import PermissionModel


def main(filename: str):
    print(f'Open {filename}')
    with open(filename) as f:
        slugs_lines = f.read()
        slugs_list = slugs_lines.split('\n')

    make_permissions(slugs_list)


def make_permissions(permission_names_list: list[str]) -> list[PermissionModel]:
    """
    Создание CRUD-прав по списку имён для них

    Args:
        permission_names_list: список имён

    Returns:
         None
    """
    perms = []

    for perm_name in permission_names_list:
        if not perm_name:
            continue

        perms_items = PermissionModel.create_permissions(perm_name)
        perms.extend(perms_items)

    print('Создание CRUD-прав в БД завершено')
    return perms


if __name__ == '__main__':
    filename = sys.argv[1] if len(sys.argv) == 2 else './slugs'
    main(filename)
