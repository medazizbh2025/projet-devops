from . import db

class Salle(db.Model):
    __tablename__ = 'salles'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    capacite = db.Column(db.Integer, nullable=False)
    equipements = db.Column(db.JSON, nullable=False, default=list)
    active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "capacite": self.capacite,
            "equipements": self.equipements,
            "active": self.active
        }