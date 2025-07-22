from django.shortcuts import redirect, render
from django.views import View, generic
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required, login_required
from catalog.models import Book, Author, BookInstance, Genre
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
        ).filter(status__exact=constants.LoanStatus.ON_LOAN.value).order_by('due_back')


@login_required
@permission_required('catalog.can_mark_returned')
def mark_returned(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)
    book_instance.status = constants.LoanStatus.AVAILABLE.value
    book_instance.borrower = None
    book_instance.due_back = None
    book_instance.save()
    return redirect('my-borrowed')
