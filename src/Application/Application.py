from src.Database.Database import Database


class Application:
    database = Database()

    def __init__(self):
        pass

    def run(self):
        self.database.create()
