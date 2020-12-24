from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .form import EmailPostForm, CommentForm, SearchForm
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B')
            search_query = SearchQuery(query)
            results = Post.published.annotate(search=search_vector, rank=SearchRank(search_vector, search_query)).filter(rank__gte=0.3).order_by('-rank')
    return render(request, 
                'blog/post/search.html', 
                {'form': form,                                
                'query': query, 
                'results': results})

def post_share(request, post_id):           #ovo je ustvari definisanje jednog prikaza, koji prihvata objekat request i promenljivu post_id
    # Vraca post po ID-u
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False

    if request.method == 'POST':
        # Forma je dostavljena
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Form polja prolaze da su validna
            cd = form.cleaned_data
            post_url = request.build_absolute_url(post.get_absolute_url())
            subject = f"{cd['name']} recommends you red " f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'djurdjev.zarko@gmail.com', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post' : post, 'form' : form, 'sent' : sent})
class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'

def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 3) # 3 posta na svakoj stranici
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # Ako stranica nije intiger daje nam prvu stranicu
        posts = paginator.page(1)
    except EmptyPage:
        # Ako stranica je izvan dosega daje nam zadnju stranicu rezultata
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/post/list.html', {'page': page, 'posts': posts, 'tag': tag})

def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post, status='published', publish__year=year, publish__month=month, publish__day=day)
    # Lista aktivnih komentara za post 
    comments = post.comments.filter(active=True)

    new_comment = None

    if request.method == 'POST':
        # Comment je objavljen
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Napravi Comment objekat ali nemoj ga jos sacuvati u bazu podataka
            new_comment = comment_form.save(commit=False)
            # Dodeli post komentaru
            new_comment.post = post
            # Sacuvaj komentar u bazu
            new_comment.save()
    else:
        comment_form = CommentForm()

    # Lista slicnih postova
    post_tags_id = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_id).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]

    return render(request, 'blog/post/detail.html', {'post': post, 'comments': comments, 'new_comment': new_comment, 'comment_form': comment_form, 'similar_posts': similar_posts})

# Create your views here.
