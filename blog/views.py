from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from .form import EmailPostForm, CommentForm
from django.core.mail import send_mail

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

def post_list(request):
    object_list = Post.published.all()
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
    return render(request, 'blog/post/list.html', {'page': page, 'posts': posts})

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
    return render(request, 'blog/post/detail.html', {'post': post, 'comments': comments, 'new_comment': new_comment, 'comment_form': comment_form})

# Create your views here.
