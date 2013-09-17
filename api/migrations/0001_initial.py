# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Classgroup'
        db.create_table(u'api_classgroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='created_classgroups', null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'api', ['Classgroup'])

        # Adding M2M table for field users on 'Classgroup'
        m2m_table_name = db.shorten_name(u'api_classgroup_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('classgroup', models.ForeignKey(orm[u'api.classgroup'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['classgroup_id', 'user_id'])

        # Adding model 'Resource'
        db.create_table(u'api_resource', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='resources', to=orm['auth.User'])),
            ('classgroup', self.gf('django.db.models.fields.related.ForeignKey')(related_name='resources', to=orm['api.Classgroup'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('resource_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('data', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('approved', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'api', ['Resource'])

        # Adding model 'Message'
        db.create_table(u'api_message', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('reply_to', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='replies', null=True, on_delete=models.SET_NULL, to=orm['api.Message'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='messages', to=orm['auth.User'])),
            ('classgroup', self.gf('django.db.models.fields.related.ForeignKey')(related_name='messages', to=orm['api.Classgroup'])),
            ('approved', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'api', ['Message'])

        # Adding M2M table for field resources on 'Message'
        m2m_table_name = db.shorten_name(u'api_message_resources')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('message', models.ForeignKey(orm[u'api.message'], null=False)),
            ('resource', models.ForeignKey(orm[u'api.resource'], null=False))
        ))
        db.create_unique(m2m_table_name, ['message_id', 'resource_id'])

        # Adding model 'Rating'
        db.create_table(u'api_rating', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rating', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('message', self.gf('django.db.models.fields.related.ForeignKey')(related_name='ratings', to=orm['api.Message'])),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='ratings', null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'api', ['Rating'])

        # Adding model 'ClassSettings'
        db.create_table(u'api_classsettings', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('classgroup', self.gf('django.db.models.fields.related.OneToOneField')(blank=True, related_name='class_settings', unique=True, null=True, to=orm['api.Classgroup'])),
            ('is_public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('moderate_posts', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('access_key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('allow_signups', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'api', ['ClassSettings'])

        # Adding model 'Tag'
        db.create_table(u'api_tag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('classgroup', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tags', to=orm['api.Classgroup'])),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'api', ['Tag'])

        # Adding M2M table for field messages on 'Tag'
        m2m_table_name = db.shorten_name(u'api_tag_messages')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tag', models.ForeignKey(orm[u'api.tag'], null=False)),
            ('message', models.ForeignKey(orm[u'api.message'], null=False))
        ))
        db.create_unique(m2m_table_name, ['tag_id', 'message_id'])

        # Adding model 'UserProfile'
        db.create_table(u'api_userprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(blank=True, related_name='profile', unique=True, null=True, to=orm['auth.User'])),
            ('image', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True, null=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'api', ['UserProfile'])

        # Adding model 'EmailSubscription'
        db.create_table(u'api_emailsubscription', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email_address', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=255, db_index=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'api', ['EmailSubscription'])


    def backwards(self, orm):
        # Deleting model 'Classgroup'
        db.delete_table(u'api_classgroup')

        # Removing M2M table for field users on 'Classgroup'
        db.delete_table(db.shorten_name(u'api_classgroup_users'))

        # Deleting model 'Resource'
        db.delete_table(u'api_resource')

        # Deleting model 'Message'
        db.delete_table(u'api_message')

        # Removing M2M table for field resources on 'Message'
        db.delete_table(db.shorten_name(u'api_message_resources'))

        # Deleting model 'Rating'
        db.delete_table(u'api_rating')

        # Deleting model 'ClassSettings'
        db.delete_table(u'api_classsettings')

        # Deleting model 'Tag'
        db.delete_table(u'api_tag')

        # Removing M2M table for field messages on 'Tag'
        db.delete_table(db.shorten_name(u'api_tag_messages'))

        # Deleting model 'UserProfile'
        db.delete_table(u'api_userprofile')

        # Deleting model 'EmailSubscription'
        db.delete_table(u'api_emailsubscription')


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
        u'api.rating': {
            'Meta': {'object_name': 'Rating'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ratings'", 'to': u"orm['api.Message']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ratings'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'rating': ('django.db.models.fields.IntegerField', [], {'default': '0'})
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