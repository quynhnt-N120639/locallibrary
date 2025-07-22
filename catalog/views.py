from django.shortcuts import render
from django.views import generic
from django.shortcuts import get_object_or_404
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
