"""
    This file is part of Gig-o-Matic

    Gig-o-Matic is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import datetime
from django.shortcuts import get_object_or_404, render
from django.views import generic
from django.urls import reverse
from django.utils import timezone
from .models import Gig, Plan
from .forms import GigForm
from band.models import Band


class DetailView(generic.DetailView):
    model = Gig
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_can_edit'] = self.request.user.is_superuser # todo or band members, admins etc.
        context['user_can_create'] = self.request.user.is_superuser # todo or band members, admins etc.

        return context

class CreateView(generic.CreateView):
    model = Gig
    form_class = GigForm
    
    def get_success_url(self):
        return reverse('gig-detail', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_new'] = True
        context['the_band'] = Band.objects.get(id=self.kwargs['bk'])
        return context

    def form_valid(self, form):

        band = Band.objects.get(id=self.kwargs['bk'])

        # make sure we're allowed to make a gig for this band
        if self.request.user.is_superuser:
            has_permission = True
        else:
            has_permission = band.anyone_can_create_gigs or band.is_admin(self.request.user)

        if has_permission is False:
            raise(PermissionError, "Trying to create a gig without permission: {}".format(self.request.user.email))

        form.instance.band = band
        return super(CreateView, self).form_valid(form)

class UpdateView(generic.UpdateView):
    model = Gig
    form_class = GigForm
    def get_success_url(self):
        return reverse('gig-detail', kwargs={'pk': self.object.id})

def answer(request, pk, val):
    plan = get_object_or_404(Plan, pk=pk)
    plan.status = val
    if val == Plan.StatusChoices.DONT_KNOW:
        now = datetime.datetime.now(tz=timezone.get_current_timezone())
        if (future_days := (plan.gig.date - now).days) > 8:
            plan.snooze_until = now + datetime.timedelta(days=7)
        elif future_days > 2:
            plan.snooze_until = plan.gig.date - datetime.timedelta(days=2)
    plan.save()
    return render(request, 'gig/answer.html', {'gig_id': plan.gig.id})
