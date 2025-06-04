from pilgrim.database import Database


class Application:
    def __init__(self):
        self.database = Database()

    def run(self):
        self.database.create()
