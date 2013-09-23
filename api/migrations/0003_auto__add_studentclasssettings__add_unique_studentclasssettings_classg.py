# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StudentClassSettings'
        db.create_table(u'api_studentclasssettings', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('classgroup', self.gf('django.db.models.fields.related.ForeignKey')(related_name='student_class_settings', to=orm['api.Classgroup'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='student_class_settings', to=orm['auth.User'])),
            ('email_frequency', self.gf('django.db.models.fields.CharField')(default='A', max_length=3)),
        ))
        db.send_create_signal(u'api', ['StudentClassSettings'])

        # Adding unique constraint on 'StudentClassSettings', fields ['classgroup', 'user']
        db.create_unique(u'api_studentclasssettings', ['classgroup_id', 'user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'StudentClassSettings', fields ['classgroup', 'user']
        db.delete_unique(u'api_studentclasssettings', ['classgroup_id', 'user_id'])

        # Deleting model 'StudentClassSettings'
        db.delete_table(u'api_studentclasssettings')


    models = {
        u'api.classgroup': {
            'Meta': {'object_name': 'Classgroup'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'created_classgroups'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'classgroups'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"})
        },
        u'api.classsettings': {
            'Meta': {'object_name': 'ClassSettings'},
            'access_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'allow_signups': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'classgroup': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'class_settings'", 'unique': 'True', 'null': 'True', 'to': u"orm['api.Classgroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'moderate_posts': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'api.emailsubscription': {
            'Meta': {'object_name': 'EmailSubscription'},
            'email_address': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'api.message': {
            'Meta': {'object_name': 'Message'},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'classgroup': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'messages'", 'to': u"orm['api.Classgroup']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'reply_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'replies'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['api.Message']"}),
            'resources': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'messages'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['api.Resource']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'messages'", 'to': u"orm['auth.User']"})
        },
        u'api.messagenotification': {
            'Meta': {'unique_together': "(('receiving_message', 'origin_message'),)", 'object_name': 'MessageNotification'},
            'cleared': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'notification_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'origin_message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['api.Message']"}),
            'receiving_message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'received_message_notifications'", 'to': u"orm['api.Message']"}),
            'receiving_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'message_notifications'", 'to': u"orm['auth.User']"})
        },
        u'api.rating': {
            'Meta': {'object_name': 'Rating'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ratings'", 'to': u"orm['api.Message']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ratings'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'rating': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'api.ratingnotification': {
            'Meta': {'unique_together': "(('receiving_message', 'origin_rating'),)", 'object_name': 'RatingNotification'},
            'cleared': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'notification_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'origin_rating': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['api.Rating']"}),
            'receiving_message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'received_rating_notifications'", 'to': u"orm['api.Message']"}),
            'receiving_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rating_notifications'", 'to': u"orm['auth.User']"})
        },
        u'api.resource': {
            'Meta': {'object_name': 'Resource'},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'classgroup': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'resources'", 'to': u"orm['api.Classgroup']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'resources'", 'to': u"orm['auth.User']"}),
            'resource_type': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'api.studentclasssettings': {
            'Meta': {'unique_together': "(('classgroup', 'user'),)", 'object_name': 'StudentClassSettings'},
            'classgroup': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'student_class_settings'", 'to': u"orm['api.Classgroup']"}),
            'email_frequency': ('django.db.models.fields.CharField', [], {'default': "'A'", 'max_length': '3'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'student_class_settings'", 'to': u"orm['auth.User']"})
        },
        u'api.tag': {
            'Meta': {'object_name': 'Tag'},
            'classgroup': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tags'", 'to': u"orm['api.Classgroup']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'messages': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'tags'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['api.Message']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        u'api.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'profile'", 'unique': 'True', 'null': 'True', 'to': u"orm['auth.User']"})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['api']