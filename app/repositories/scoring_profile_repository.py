from sqlalchemy.orm import Session

from app.models.scoring_profile import ScoringProfile


class ScoringProfileRepository:
    def __init__(self, db: Session):
        self.db = db

    # @transition_to(ProfileStatus.ACTIVE, profile_state_machine)
    # def activate(self, profile) -> ScoringProfile:
    #     profile.activated_at = datetime.utcnow()
    #     self.db.commit()
    #     return profile

    # @transition_to(ProfileStatus.ARCHIVED, profile_state_machine)
    # def archive(self, profile) -> ScoringProfile:
    #     self.db.commit()
    #     return profile

    def get(self, profile_id: int) -> ScoringProfile | None:
        return ScoringProfile.find_by(self.db, id=profile_id)

    def create(self, new_profile: ScoringProfile) -> ScoringProfile:
        self.db.add(new_profile)
        self.db.commit()
        return new_profile

    def save(self, profile: ScoringProfile) -> ScoringProfile:
        # self.db.commit()
        profile.save(self.db)
        return profile

    def get_active_profiles(self):
        # return self.db.query(ScoringProfile).filter_by(status="active").all()
        return ScoringProfile.where(self.db, status="active").all()


#    def save(self, db: Session):
#         db.add(self)
#         db.commit()
#         # db.refresh(self)
#         return self
