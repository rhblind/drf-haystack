from haystack import indexes
from app.models import Note
import datetime

class NoteIndex(indexes.SearchIndex , indexes.Indexable):
	text=indexes.CharField(document=True , use_template=True)
	pub_date=indexes.DateTimeField(model_attr='pub_date')
	authors=indexes.CharField(model_attr='user')
	content_auto=indexes.EdgeNgramField(model_attr='content')

	def get_model(self):
		return Note

	def index_queryset(self,using=None):
	    return self.get_model().objects.filter(pub_date__lte=datetime.datetime.now())	
