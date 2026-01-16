import shutil

from file_operations.file_operation import FileOperation

class MoveOperation(FileOperation):
    def do_task(self):
        for file_path in self.files_for_task:
            # Переміщуємо тільки файли, ігноруємо папку призначення, якщо вона всередині джерела
            if file_path.is_file() and file_path.parent.resolve() != self.target_directory.resolve():
                target_file_path = self.target_directory / file_path.name
                print(f"Moving: {file_path} -> {self.target_directory}", end=" ", flush=True)

                try:
                    # shutil.move приймає Path об'єкти напряму
                    shutil.move(file_path, target_file_path)
                    print("[OK]")
                except Exception as e:
                    print(f"[ERROR] {e.__class__.__name__}: {e}", end=" ", flush=True)


