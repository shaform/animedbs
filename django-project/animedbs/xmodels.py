from django.db import connection, transaction

class ObjectXModel(object):
    pass


class AnimeXModel(ObjectXModel):
    def __init__(self, row):
        self.Id = row[0]
        self.Title = row[1]
        self.Authored_by = row[2]
        self.Description = row[3]
        self.Web_address = row[4]

    @classmethod
    def getOneXModel(cls, Ids):
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM `ANIME` WHERE `Id` = %s;', Ids)
        row = cursor.fetchone()
        if row:
            return AnimeXModel(row)
        else:
            return None
