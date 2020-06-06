# Contributor Guide
Please report any bug or question by [opening an issue](https://help.github.com/en/github/managing-your-work-on-github/creating-an-issue).
Pull requests for new features, improvements, and bug fixes are very welcome!

The application is structured according to a variant of the
[model-view-controller architecture](https://martinfowler.com/eaaDev/uiArchs.html).
To understand the relationship of the model, view, and controller have a look
at how each of them is instantiated in `__main__.py`. For
example, the view class has references to the model class as well as the
controller class, whereas the model has no reference to any of the other
components of the architecture (i.e., the model is agnostic to the view and
controller).
