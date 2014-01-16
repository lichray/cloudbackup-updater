%{!?pyver: %define pyver %(%{__python2} -c "import sys; print sys.version[:3]")}

Name:           cloudbackup-updater
Version:        0.1
Release:        1
Summary:        Auto-updater for the Rackspace Cloud Backup agent

Group:          Applications/System
License:        BSD
URL:            https://github.com/lichray/cloudbackup-updater
Source0:        %{name}-%{version}.tar.xz

BuildArch:      noarch
BuildRequires:  python-devel, python-setuptools
Requires:       python-daemon, python-requests

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
%{__python2} setup.py build


%install
%{__python2} setup.py install -O1 --skip-build --root %{buildroot}
install -D -m 755 redhat/%{name} %{buildroot}%{_sysconfdir}/init.d/%{name}


%post
if [ -x /usr/lib/lsb/install_initd ]; then
  /usr/lib/lsb/install_initd /etc/init.d/%{name}
elif [ -x /sbin/chkconfig ]; then
  /sbin/chkconfig --add %{name}
else
  echo "Unable to setup init scripts"
fi


%preun
if [ $1 -eq 0 ] ; then
  /sbin/service %{name} stop >/dev/null 2>&1
  if [ -x /usr/lib/lsb/remove_initd ]; then
    /usr/lib/lsb/install_initd /etc/init.d/%{name}
  elif [ -x /sbin/chkconfig ]; then
    /sbin/chkconfig --del %{name}
  fi
fi


%files
%{_bindir}/%{name}
%{python_sitelib}/cloudbackup_updater/
%{python_sitelib}/cloudbackup_updater-%{version}-py%{pyver}.egg-info/
%config(noreplace) %{_sysconfdir}/init.d/%{name}

%changelog
* Mon Jan 13 2014 Zhihao Yuan <zhihao.yuan@rackspace.com> - 0.1-1
- Initial package
