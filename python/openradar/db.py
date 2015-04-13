import models

class Radar():
    def fetchAll(self, page = 1, count = 100):
        return models.Radar.gql("ORDER BY number DESC").fetch(count, offset=(page - 1) * count)
        
    def fetchCount(self):
        return models.Radar.all().count(limit=100000)
        
    def fetchById(self, id):
        return models.Radar.get_by_id(id)
        
    def fetchByNumber(self, number):
        return models.Radar.gql("WHERE number = :1", number).get()
        
    def fetchByNumbers(self, numbers, page = 1, count = 100):
        return models.Radar.gql("WHERE number IN :1", numbers).fetch(count, offset=(page - 1) * count)
        
    def fetchByUser(self, user, page = 1, count = 100):
        return models.Radar.gql("WHERE user = :1 ORDER BY number DESC", user).fetch(count, offset=(page - 1) * count)
        
    def fetchByUsers(self, users, page = 1, count = 100):
        return models.Radar.gql("WHERE user IN :1 ORDER BY number DESC", users).fetch(count, offset=(page - 1) * count)
        
class Comment():
    def fetchAll(self, page = 1, count = 100):
        return models.Comment.gql("ORDER BY posted_at DESC").fetch(count, offset=(page - 1) * count)
        
    def fetchCount(self):
        return models.Comment.all().count(limit=100000)
        
    def fetchByUser(self, user, page = 1, count = 100):
        return models.Comment.gql("WHERE user = :1 ORDER BY posted_at DESC", user).fetch(count, offset=(page - 1) * count)
        
class APIKey():
    def fetchByUser(self, user):
        return models.APIKey.gql("WHERE user = :1", user).get()

    def fetchByAPIKey(self, apikey):
        return models.APIKey.gql("WHERE apikey = :1", apikey).get()
    
