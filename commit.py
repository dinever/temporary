from dulwich.objects import Blob
from dulwich.objects import Commit

spam = Blob.from_string("My new file content\n")
print spam.id

blob = Blob()
blob.data = "My new file content\n"
print blob.id

c1 = Commit()
