%{!?__python2: %define __python2 %{__python}}

Name:           cloudbackup-updater
Version:        1.2
Release:        1
Summary:        Auto-updater for the Rackspace Cloud Backup agent

Group:          Applications/System
License:        BSD
URL:            https://github.com/lichray/cloudbackup-updater
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  zip
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
Cloud Backup Agent auto-updater operates in 2 modes:

  1. Daemon mode (with the -d commend line option);
  2. One-shot update (without -d).

In each mode, the auto-updater can add the agent repository
if it's not there, install the agent if not installed, and
update the agent if a new version is released.


%prep
%setup -q


%build
zip -r %{name}.zip cloudbackup_updater


%install
install -D -m 644 %{name}.zip %{buildroot}%{_datadir}/%{name}/%{name}.zip
install -D -m 755 redhat/%{name} %{buildroot}%{_sysconfdir}/init.d/%{name}
install -D -m 755 scripts/%{name} %{buildroot}%{_bindir}/%{name}


%post
function can_start_service()
{
  local current_runlevel=`grep runlevel | awk '{print $2}'`
  local available_runlevels=`grep '# chkconfig:' /etc/init.d/$1 | awk '{print $3}'`
  [[ available_runlevels == *"$current_runlevel"* ]]
}

if [ -x /sbin/chkconfig ]; then
  /sbin/chkconfig --add %{name}

  if can_start_service %{name}; then
    if [ $1 -eq 1 ]; then   # install
      /sbin/service %{name} start
    else                    # upgrade
      /sbin/service %{name} restart
    fi
  fi

else
  echo "The service does not start by default."
fi


%preun
if [ $1 -eq 0 ]; then   # uninstall
  /sbin/service %{name} stop >/dev/null 2>&1

  if [ -x /sbin/chkconfig ]; then
    /sbin/chkconfig --del %{name}
  fi
fi


%files
%{_bindir}/%{name}
%{_datadir}/%{name}/
%config(noreplace) %{_sysconfdir}/init.d/%{name}

%changelog
* Thu Dec  8 2014 Zhihao Yuan <zhihao.yuan@rackspace.com> - 1.2-1
- Update to 1.2

* Thu Oct  2 2014 Zhihao Yuan <zhihao.yuan@rackspace.com> - 1.1-1
- Update to 1.1

* Wed Jun  4 2014 Zhihao Yuan <zhihao.yuan@rackspace.com> - 1.0-2
- Update to 1.0

* Tue Jan 28 2014 Zhihao Yuan <zhihao.yuan@rackspace.com> - 0.1-2
- No longer install as a standard python package

* Mon Jan 13 2014 Zhihao Yuan <zhihao.yuan@rackspace.com> - 0.1-1
- Initial package
