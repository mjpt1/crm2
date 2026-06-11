from accounts.models import User


class RoundRobinAssigner:
    """
    الگوریتم تخصیص خودکار لید به کارشناس.
    اولویت: آنلاین بودن → کمترین لید فعال → ظرفیت خالی.
    """

    @staticmethod
    def get_candidate_pool(supervisor=None):
        qs = User.objects.filter(role=User.EXPERT, is_active=True)
        if supervisor:
            qs = qs.filter(supervisor=supervisor)
        return qs

    @staticmethod
    def find_best_expert(supervisor=None):
        candidates = RoundRobinAssigner.get_candidate_pool(supervisor)

        online = candidates.filter(is_online=True)
        pool = online if online.exists() else candidates

        best = None
        min_count = float('inf')

        for expert in pool:
            count = expert.current_lead_count
            if count < expert.max_capacity and count < min_count:
                min_count = count
                best = expert

        return best

    @classmethod
    def assign(cls, lead, supervisor=None):
        expert = cls.find_best_expert(supervisor)
        if expert:
            lead.assigned_to = expert
            lead.save(update_fields=['assigned_to'])
        return expert
