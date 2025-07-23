import datetime
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View, generic
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import permission_required, login_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from catalog.models import Book, Author, BookInstance, Genre
from catalog.forms import RenewBookModelForm
from . import constants


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.count()
    num_instances = BookInstance.objects.count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(
        status=constants.LoanStatus.AVAILABLE
    ).count()
    # The 'all()' is implied by default.
    num_authors = Author.objects.count()
    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 1)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


class BookListView(generic.ListView):
    model = Book
    # your own name for the list as a template variable
    context_object_name = 'book_list'
    # Specify your own templatename/location
    template_name = 'catalog/book_list.html'
    paginate_by = constants.BOOKS_PER_PAGE_MAX

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(BookListView, self).get_context_data(**kwargs)
        return context


class BookDetailView(generic.DetailView):  # Cach 1: Class-Based Views
    model = Book

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['STATUS_AVAILABLE'] = constants.LoanStatus.AVAILABLE.value
        context['STATUS_MAINTENANCE'] = constants.LoanStatus.MAINTENANCE.value
        return context


def book_detail_view(request, pk):  # Cach 2: Function-Based Views
    book = get_object_or_404(Book, pk=pk)
    return render(request, 'catalog/book_detail.html', context={'book': book})


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = constants.BOOKS_PER_PAGE_MAX

    def get_queryset(self):
        return BookInstance.objects.filter(
                borrower=self.request.user
            ).filter(status__exact=constants.LoanStatus.ON_LOAN.value
            ).order_by('due_back')


class AllBorrowedBooksListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    permission_required = 'catalog.can_mark_returned'

    def get_queryset(self):
        return BookInstance.objects.filter(
            status__exact=constants.LoanStatus.ON_LOAN.value).order_by('due_back')


@login_required
@permission_required('catalog.can_mark_returned')
def mark_returned(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)
    book_instance.status = constants.LoanStatus.AVAILABLE.value
    book_instance.borrower = None
    book_instance.due_back = None
    book_instance.save()
    return redirect('my-borrowed')


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':
        form = RenewBookModelForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the modeldue_back field)
            book_instance.due_back = form.cleaned_data['due_back']
            book_instance.save()
            return HttpResponseRedirect(reverse('all-borrowed'))
    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookModelForm(initial={'due_back': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }
    return render(request, 'catalog/book_renew_librarian.html', context)


class AuthorListView(generic.ListView):
    model = Author
    content_object_name = 'author_list'
    template_name = 'catalog/author_list.html'
    paginate_by = constants.AUTHORS_PER_PAGE_MAX


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class AuthorCreate(StaffRequiredMixin, CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': constants.INITIAL_DEADTH_DATE_OF_AUTHOR}
    success_url = reverse_lazy('authors')


class AuthorUpdate(StaffRequiredMixin, UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    success_url = reverse_lazy('authors')


class AuthorDelete(StaffRequiredMixin, DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
