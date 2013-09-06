# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Tweet'
        db.create_table(u'api_tweet', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=160)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('id_str', self.gf('django.db.models.fields.CharField')(unique=True, max_length=35, db_index=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('retweet_of', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='retweets', null=True, to=orm['api.Tweet'])),
            ('reply_to', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='replies', null=True, to=orm['api.Tweet'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tweets', to=orm['auth.User'])),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'api', ['Tweet'])

        # Adding model 'Tag'
        db.create_table(u'api_tag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=160, db_index=True)),
        ))
        db.send_create_signal(u'api', ['Tag'])

        # Adding M2M table for field tweets on 'Tag'
        m2m_table_name = db.shorten_name(u'api_tag_tweets')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tag', models.ForeignKey(orm[u'api.tag'], null=False)),
            ('tweet', models.ForeignKey(orm[u'api.tweet'], null=False))
        ))
        db.create_unique(m2m_table_name, ['tag_id', 'tweet_id'])

        # Adding M2M table for field users on 'Tag'
        m2m_table_name = db.shorten_name(u'api_tag_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tag', models.ForeignKey(orm[u'api.tag'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['tag_id', 'user_id'])

        # Adding model 'UserProfile'
        db.create_table(u'api_userprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(blank=True, related_name='profile', unique=True, null=True, to=orm['auth.User'])),
            ('twitter_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('twitter_id_str', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30, db_index=True)),
            ('twitter_screen_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'api', ['UserProfile'])


    def backwards(self, orm):
        # Deleting model 'Tweet'
        db.delete_table(u'api_tweet')

        # Deleting model 'Tag'
        db.delete_table(u'api_tag')

        # Removing M2M table for field tweets on 'Tag'
        db.delete_table(db.shorten_name(u'api_tag_tweets'))

        # Removing M2M table for field users on 'Tag'
        db.delete_table(db.shorten_name(u'api_tag_users'))

        # Deleting model 'UserProfile'
        db.delete_table(u'api_userprofile')


    models = {
        u'api.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '160', 'db_index': 'True'}),
            'tweets': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'tags'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['api.Tweet']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'tags'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"})
        },
        u'api.tweet': {
            'Meta': {'object_name': 'Tweet'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_str': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '35', 'db_index': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'reply_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'replies'", 'null': 'True', 'to': u"orm['api.Tweet']"}),
            'retweet_of': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'retweets'", 'null': 'True', 'to': u"orm['api.Tweet']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tweets'", 'to': u"orm['auth.User']"})
        },
        u'api.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'twitter_id_str': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'}),
            'twitter_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'twitter_screen_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
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