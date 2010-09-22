import models

class Radar():
    def fetchAll(self, page = 1, count = 100):
        return models.Radar.gql("ORDER BY number DESC").fetch(count, (page - 1) * count)
        
    def fetchById(self, id):
        return models.Radar.get_by_id(id)
        
    def fetchByNumber(self, number):
        return models.Radar.gql("WHERE number = :1", number).get()
        
    def fetchByNumbers(self, numbers, page = 1, count = 100):
        return models.Radar.gql("WHERE number IN :1", numbers).fetch(count, (page - 1) * count)
        
    def fetchByUser(self, user, page = 1, count = 100):
        return models.Radar.gql("WHERE user = :1 ORDER BY number DESC", user).fetch(count, (page - 1) * count)
        
class Comment():
    def fetchAll(self, page = 1, count = 100):
        return models.Comment.gql("ORDER BY posted_at DESC").fetch(count, (page - 1) * count)
        
    def fetchByUser(self, user, page = 1, count = 100):
        return models.Comment.gql("WHERE user = :1 ORDER BY posted_at DESC", user).fetch(count, (page - 1) * count)
        

