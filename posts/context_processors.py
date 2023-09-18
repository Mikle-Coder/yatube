def following(request):
    return True #request.user.follower.filter(author__username=request.username).exsists()